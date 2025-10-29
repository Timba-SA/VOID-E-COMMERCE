# /server/workers/email_celery_task.py

import asyncio
import logging
from datetime import datetime

from imap_tools import MailBox

# Importamos la configuración central y la app de Celery
from settings import settings
from celery_worker import celery_app

# Importamos los servicios que necesitamos
from services import ia_services, email_service
from services.ia_services import IAServiceError
from database import database
from database.models import EmailTask, ConversacionIA
from sqlalchemy import select, update

# Configuración del logger con formato mejorado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def check_and_process_emails():
    """
    Función principal reescrita con imap-tools para ser más confiable.
    Se conecta, busca emails no leídos, los procesa con la IA y responde.
    Maneja errores individualmente por email.
    """
    if not all([settings.EMAIL_SENDER, settings.EMAIL_APP_PASSWORD]):
        logger.error("Email worker: Faltan variables de entorno EMAIL_SENDER o EMAIL_APP_PASSWORD.")
        return

    try:
        # Conexión IMAP
        with MailBox(settings.IMAP_SERVER).login(settings.EMAIL_SENDER, settings.EMAIL_APP_PASSWORD) as mailbox:
            # Usamos list() para obtener todos los UIDs antes de empezar a procesar
            unread_emails = list(mailbox.fetch(criteria="UNSEEN", mark_seen=False))

            if not unread_emails:
                logger.info("No hay emails nuevos para procesar.")
                return

            logger.info(f"Se encontraron {len(unread_emails)} emails nuevos.")

            # Verificamos que la fábrica de sesiones esté inicializada en este proceso
            if database.AsyncSessionLocal is None:
                logger.critical("AsyncSessionLocal no está inicializado en el proceso worker. Llamando a setup_database_engine().")
                database.setup_database_engine() # Asegura que el engine (con NullPool) exista

            # Iteramos sobre los emails obtenidos
            for msg in unread_emails:
                email_uid = getattr(msg, 'uid', 'unknown_uid') # Obtenemos el UID para logs

                # --- Abrimos una sesión POR CADA EMAIL ---
                # Esto asegura que cada email tenga su propia transacción
                async with database.AsyncSessionLocal() as db_session:
                    email_task_id = None # Para referenciarlo en logs si falla
                    try:
                        # Normalizamos remitente
                        sender = None
                        try:
                            # Intenta obtener la dirección de correo electrónico directamente
                            sender = msg.from_values.email if msg.from_values else str(msg.from_)
                        except Exception:
                            # Fallback si from_values no está disponible o falla
                            sender = str(msg.from_)

                        logger.info(f"Procesando email UID {email_uid} de {sender} (Asunto: '{msg.subject}')")

                        body = msg.text or msg.html or "" # Simplificado

                        if not body:
                            logger.warning(f"Email UID {email_uid} sin cuerpo. Marcando como leído.")
                            mailbox.flag([msg.uid], '\\Seen', True)
                            continue # Pasa al siguiente email

                        # --- Persistimos EmailTask (pending) ---
                        # Hacemos commit inicial para obtener el ID
                        email_task = EmailTask(
                            sender_email=sender,
                            subject=msg.subject,
                            body=body,
                            uid=str(email_uid), # Aseguramos que sea string
                            status='pending',
                            attempts=0
                        )
                        db_session.add(email_task)
                        ### <<< CAMBIO <<< Commit inicial para obtener el ID y marcar inicio
                        await db_session.commit()
                        await db_session.refresh(email_task)
                        email_task_id = email_task.id # Guardamos ID para logs
                        logger.info(f"EmailTask id={email_task_id} creado para UID {email_uid}")

                        # Marcamos como processing y aumentamos attempts
                        await db_session.execute(
                            update(EmailTask)
                            .where(EmailTask.id == email_task_id)
                            .values(status='processing', attempts=EmailTask.attempts + 1)
                        )
                        ### <<< CAMBIO <<< Commit para actualizar estado a 'processing'
                        await db_session.commit()

                        # --- Lógica de IA mejorada ---
                        CONTEXT_TURNS_LIMIT = 5
                        result = await db_session.execute(
                            select(ConversacionIA)
                            .where(ConversacionIA.sesion_id == sender)
                            .order_by(ConversacionIA.creado_en)
                        )
                        full_db_history = result.scalars().all()
                        limited_history = full_db_history[-(CONTEXT_TURNS_LIMIT * 2):]

                        intention_analysis = await ia_services.analyze_user_intention(body)
                        logger.info(f"Intención detectada (UID {email_uid}): {intention_analysis['primary_intention']}")

                        catalog = await ia_services.get_enhanced_catalog_from_db(db_session, body)

                        if intention_analysis["primary_intention"] == "product_search":
                            search_result = await ia_services.smart_product_search(db_session, body, limit=4)
                            if search_result["products"]:
                                matched_lines = ["\n--- PRODUCTOS ESPECÍFICOS PARA TU CONSULTA ---"]
                                for prod in search_result["products"]:
                                    stock_info = "Sin stock"
                                    if hasattr(prod, 'variantes') and prod.variantes:
                                        total_stock = sum(v.cantidad_en_stock for v in prod.variantes if v.cantidad_en_stock is not None) # Suma segura
                                        if total_stock > 0:
                                            available_sizes = [v.tamanio for v in prod.variantes if v.cantidad_en_stock is not None and v.cantidad_en_stock > 0]
                                            stock_info = f"Stock: {total_stock}"
                                            if available_sizes:
                                                stock_info += f" | Talles: {', '.join(sorted(list(set(available_sizes))))}" # Ordenado y único

                                    category = prod.categoria.nombre if getattr(prod, 'categoria', None) else 'Sin categoría'
                                    matched_lines.append(
                                        f"🎯 ID: {prod.id} | {prod.nombre} | Cat: {category} | "
                                        f"{prod.color or 'N/A'} | ${prod.precio:.2f} | {stock_info}" # Formato precio
                                    )
                                matched_lines.append("--- FIN PRODUCTOS ESPECÍFICOS ---")
                                catalog = "\n".join(matched_lines) + "\n\n" + catalog # Doble salto

                        recommendations = await ia_services.get_personalized_recommendations(db_session, sender, limit=3)
                        if recommendations:
                            rec_lines = ["\n--- PRODUCTOS RECOMENDADOS PARA VOS ---"]
                            for rec in recommendations:
                                stock_info = "Sin stock"
                                if hasattr(rec, 'variantes') and rec.variantes:
                                    total_stock = sum(v.cantidad_en_stock for v in rec.variantes if v.cantidad_en_stock is not None)
                                    if total_stock > 0:
                                        available_sizes = [v.tamanio for v in rec.variantes if v.cantidad_en_stock is not None and v.cantidad_en_stock > 0]
                                        stock_info = f"Stock: {total_stock}"
                                        if available_sizes:
                                            stock_info += f" | Talles: {', '.join(sorted(list(set(available_sizes))))}"
                                rec_lines.append(
                                    f"⭐ ID: {rec.id} | {rec.nombre} | ${rec.precio:.2f} | {stock_info}"
                                )
                            rec_lines.append("--- FIN RECOMENDACIONES ---")
                            catalog += "\n" + "\n".join(rec_lines) # Separador

                        user_preferences = ia_services.analyze_user_preferences(limited_history)
                        system_prompt = ia_services.get_enhanced_system_prompt(user_preferences, intention_analysis)

                        ai_response = "" # Inicializar por si falla la IA
                        try:
                            ai_response = await ia_services.get_ia_response(
                                system_prompt=system_prompt,
                                catalog_context=catalog,
                                chat_history=limited_history,
                                user_prompt=f"Email recibido: {body}"
                            )
                        except IAServiceError as e_ia:
                            logger.error(f"La IA falló para EmailTask id={email_task_id} (UID {email_uid}): {e_ia}")
                            ai_response = ( # Respuesta genérica de fallback
                                "¡Hola! Gracias por tu mensaje. Soy Kara de VOID Indumentaria.\n\n"
                                "En este momento estoy teniendo dificultades para procesar tu consulta automáticamente, "
                                "pero no te preocupes, nuestro equipo humano ya fue notificado y te responderá lo antes posible.\n\n"
                                "¡Que tengas un buen día!\nVOID Indumentaria"
                            )
                            # Actualizamos el estado a 'failed' para indicar problema de IA
                            await db_session.execute(
                                update(EmailTask)
                                .where(EmailTask.id == email_task_id)
                                .values(status='failed', response=f"IA Error: {e_ia}", procesado_en=datetime.utcnow())
                            )
                            ### <<< CAMBIO <<< Commit para marcar fallo de IA
                            await db_session.commit()
                            # NO enviamos email de fallback, dejamos que el humano intervenga
                            # Pero sí marcamos el email como leído para no reprocesarlo automáticamente
                            mailbox.flag([msg.uid], '\\Seen', True)
                            logger.warning(f"EmailTask id={email_task_id} (UID {email_uid}) marcado como 'failed' por error de IA. Email marcado como leído.")
                            continue # Pasamos al siguiente email

                        # --- Envío de respuesta y finalización OK ---
                        await email_service.send_plain_email(sender, f"Re: {msg.subject or 'Consulta VOID'}", ai_response)

                        # Guardamos la respuesta y marcamos done
                        await db_session.execute(
                            update(EmailTask)
                            .where(EmailTask.id == email_task_id)
                            .values(status='done', response=ai_response, procesado_en=datetime.utcnow())
                        )

                        # Guardamos la conversación SIEMPRE, incluso si la IA falló antes (guardamos el prompt)
                        conv = ConversacionIA(sesion_id=sender, prompt=body, respuesta=ai_response)
                        db_session.add(conv)

                        ### <<< CAMBIO <<< Commit final para marcar 'done' y guardar ConversacionIA
                        await db_session.commit()

                        # Marcamos como leído en el servidor IMAP SÓLO SI TODO FUE BIEN
                        mailbox.flag([msg.uid], '\\Seen', True)
                        logger.info(f"EmailTask id={email_task_id} (UID {email_uid}) procesado OK. Email marcado como leído.")

                        # Esperamos antes del siguiente para no saturar APIs externas (IA, Email)
                        # El wait va *después* de marcar como leído, por si falla el sleep
                        logger.info("Esperando 30 segundos antes del siguiente email...")
                        await asyncio.sleep(30)

                    ### <<< CAMBIO <<< Bloque except para manejar errores por email
                    except Exception as e_email:
                        logger.exception(f"Error GRANDE procesando email UID {email_uid} (Task id={email_task_id}): {e_email}")
                        # Intentamos hacer rollback de la transacción de este email
                        try:
                            await db_session.rollback()
                            logger.info(f"Rollback exitoso para la transacción del email UID {email_uid}")
                            # Si el EmailTask se llegó a crear, lo marcamos como 'failed' en una nueva transacción
                            if email_task_id:
                                async with database.AsyncSessionLocal() as error_session:
                                    await error_session.execute(
                                        update(EmailTask)
                                        .where(EmailTask.id == email_task_id)
                                        .values(status='failed', response=f"Processing Error: {str(e_email)[:1000]}") # Truncamos error
                                    )
                                    await error_session.commit()
                                    logger.warning(f"EmailTask id={email_task_id} (UID {email_uid}) marcado como 'failed' debido a excepción.")
                        except Exception as e_rollback:
                            logger.critical(f"FALLÓ EL ROLLBACK para email UID {email_uid}: {e_rollback}")
                        # NO marcamos el email como leído en IMAP, para que se reintente en la próxima ejecución

                        # Podríamos agregar un sleep aquí también si los errores son muy seguidos
                        # await asyncio.sleep(10)

    except Exception as e_fatal:
        logger.critical(f"Error FATAL en check_and_process_emails (conexión IMAP?): {e_fatal}", exc_info=True)
        raise # Re-lanzamos para que Celery maneje el retry de la tarea


@celery_app.task(name='tasks.process_unread_emails',
                  autoretry_for=(Exception,), # Reintenta ante cualquier excepción
                  retry_kwargs={'max_retries': 5, 'countdown': 60}, # 5 reintentos, esperando 1 min
                  retry_backoff=True, # Espera exponencialmente más tiempo entre reintentos
                  time_limit=300 # Máximo 5 minutos por ejecución de tarea
                 )
def process_unread_emails_task():
    """ Tarea de Celery que llama a la lógica async. """
    logger.info("Iniciando la tarea periódica de revisión de emails.")
    try:
        asyncio.run(check_and_process_emails())
        logger.info("Tarea periódica de revisión de emails finalizada con éxito.")
    except Exception as e:
        logger.critical(f"La tarea 'process_unread_emails_task' falló gravemente: {e}", exc_info=True)
        raise # Re-lanzamos para que Celery haga el retry


# La tarea 'reprocess_email_task' queda igual, ya que maneja un solo ID
@celery_app.task(name='tasks.reprocess_email_task',
                  autoretry_for=(Exception,),
                  retry_kwargs={'max_retries': 3, 'countdown': 30},
                  retry_backoff=True,
                  time_limit=180 # 3 minutos máx
                 )
def reprocess_email_task(email_task_id: int):
    """ Reprocesa un EmailTask específico por ID. """
    logger.info(f"Iniciando reprocess de EmailTask id={email_task_id}")

    async def _do_reprocess():
        if database.AsyncSessionLocal is None:
            logger.info("Reprocess: Configurando engine para este worker.")
            database.setup_database_engine()

        async with database.AsyncSessionLocal() as db_session:
            et = await db_session.get(EmailTask, email_task_id) # Usar get es más directo por PK
            if not et:
                logger.error(f"Reprocess: EmailTask id={email_task_id} no encontrado.")
                return

            logger.info(f"Reprocess: EmailTask id={email_task_id} encontrado. Estado actual: {et.status}")

            # Marcamos como 'reprocessing' y aumentamos attempts
            await db_session.execute(
                update(EmailTask)
                .where(EmailTask.id == email_task_id)
                .values(status='reprocessing', attempts=EmailTask.attempts + 1)
            )
            await db_session.commit()
            logger.info(f"Reprocess: EmailTask id={email_task_id} marcado como 'reprocessing'.")


            # --- Lógica de IA (igual que en check_and_process_emails) ---
            sender = et.sender_email
            body = et.body
            CONTEXT_TURNS_LIMIT = 5
            res_hist = await db_session.execute(
                select(ConversacionIA)
                .where(ConversacionIA.sesion_id == sender)
                .order_by(ConversacionIA.creado_en)
            )
            full_db_history = res_hist.scalars().all()
            limited_history = full_db_history[-(CONTEXT_TURNS_LIMIT * 2):]

            intention_analysis = await ia_services.analyze_user_intention(body)
            catalog = await ia_services.get_enhanced_catalog_from_db(db_session, body)

            if intention_analysis["primary_intention"] == "product_search":
                 search_result = await ia_services.smart_product_search(db_session, body, limit=4)
                 if search_result["products"]:
                    # (Misma lógica de formato de catálogo que arriba)
                    matched_lines = ["\n--- PRODUCTOS ESPECÍFICOS PARA TU CONSULTA ---"]
                    for prod in search_result["products"]:
                        stock_info = "Sin stock"
                        if hasattr(prod, 'variantes') and prod.variantes:
                            total_stock = sum(v.cantidad_en_stock for v in prod.variantes if v.cantidad_en_stock is not None)
                            if total_stock > 0:
                                available_sizes = [v.tamanio for v in prod.variantes if v.cantidad_en_stock is not None and v.cantidad_en_stock > 0]
                                stock_info = f"Stock: {total_stock}"
                                if available_sizes:
                                    stock_info += f" | Talles: {', '.join(sorted(list(set(available_sizes))))}"
                        category = prod.categoria.nombre if getattr(prod, 'categoria', None) else 'Sin categoría'
                        matched_lines.append(f"🎯 ID: {prod.id} | {prod.nombre} | Cat: {category} | {prod.color or 'N/A'} | ${prod.precio:.2f} | {stock_info}")
                    matched_lines.append("--- FIN PRODUCTOS ESPECÍFICOS ---")
                    catalog = "\n".join(matched_lines) + "\n\n" + catalog

            recommendations = await ia_services.get_personalized_recommendations(db_session, sender, limit=3)
            if recommendations:
                 # (Misma lógica de formato de recomendaciones que arriba)
                rec_lines = ["\n--- PRODUCTOS RECOMENDADOS PARA VOS ---"]
                for rec in recommendations:
                    stock_info = "Sin stock"
                    if hasattr(rec, 'variantes') and rec.variantes:
                        total_stock = sum(v.cantidad_en_stock for v in rec.variantes if v.cantidad_en_stock is not None)
                        if total_stock > 0:
                            available_sizes = [v.tamanio for v in rec.variantes if v.cantidad_en_stock is not None and v.cantidad_en_stock > 0]
                            stock_info = f"Stock: {total_stock}"
                            if available_sizes:
                                stock_info += f" | Talles: {', '.join(sorted(list(set(available_sizes))))}"
                    rec_lines.append(f"⭐ ID: {rec.id} | {rec.nombre} | ${rec.precio:.2f} | {stock_info}")
                rec_lines.append("--- FIN RECOMENDACIONES ---")
                catalog += "\n" + "\n".join(rec_lines)

            user_preferences = ia_services.analyze_user_preferences(limited_history)
            system_prompt = ia_services.get_enhanced_system_prompt(user_preferences, intention_analysis)

            ai_response = ""
            try:
                ai_response = await ia_services.get_ia_response(
                    system_prompt=system_prompt,
                    catalog_context=catalog,
                    chat_history=limited_history,
                    user_prompt=f"Email recibido: {body}"
                )
            except IAServiceError as e_ia_reprocess:
                logger.error(f"Reprocess: La IA falló para EmailTask id={email_task_id}: {e_ia_reprocess}")
                ai_response = ( # Usamos la misma respuesta genérica
                    "¡Hola! Gracias por escribirnos de nuevo. Soy Kara de VOID Indumentaria.\n\n"
                    "Lamento informarte que sigo teniendo problemas para procesar tu consulta anterior automáticamente. "
                    "Ya he alertado al equipo humano para que le dé prioridad a tu caso.\n\n"
                    "Disculpá las molestias.\nVOID Indumentaria"
                )
                # Actualizamos a 'failed'
                await db_session.execute(
                    update(EmailTask)
                    .where(EmailTask.id == email_task_id)
                    .values(status='failed', response=f"IA Reprocess Error: {e_ia_reprocess}", procesado_en=datetime.utcnow())
                )
                await db_session.commit()
                logger.warning(f"Reprocess: EmailTask id={email_task_id} marcado como 'failed' por error de IA.")
                # No reenviamos el email de fallback en este caso tampoco
                return # Terminamos el reproceso aquí si la IA falló

            # --- Envío y finalización OK del reprocess ---
            await email_service.send_plain_email(sender, f"Re: {et.subject or 'Consulta VOID (Reprocesada)'}", ai_response)

            await db_session.execute(
                update(EmailTask)
                .where(EmailTask.id == email_task_id)
                .values(status='done', response=ai_response, procesado_en=datetime.utcnow())
            )

            # Guardamos la conversación (incluso si la IA falló antes y usamos fallback)
            conv = ConversacionIA(sesion_id=sender, prompt=body, respuesta=ai_response)
            db_session.add(conv)

            await db_session.commit()
            logger.info(f"Reprocess: EmailTask id={email_task_id} completado y marcado como 'done'.")

    try:
        asyncio.run(_do_reprocess())
    except Exception as e:
        logger.exception(f"Error GRANDE reprocessando EmailTask id={email_task_id}: {e}")
        # Intentamos marcar como failed si explota feo
        try:
            async def _mark_failed():
                 if database.AsyncSessionLocal is None: database.setup_database_engine()
                 async with database.AsyncSessionLocal() as error_session:
                     await error_session.execute(
                         update(EmailTask)
                         .where(EmailTask.id == email_task_id)
                         .values(status='failed', response=f"Reprocess Fatal Error: {str(e)[:1000]}")
                     )
                     await error_session.commit()
            asyncio.run(_mark_failed())
            logger.warning(f"Reprocess: EmailTask id={email_task_id} marcado como 'failed' debido a excepción fatal.")
        except Exception as e_mark:
             logger.critical(f"Reprocess: NO SE PUDO MARCAR COMO FAILED EmailTask id={email_task_id} tras error fatal: {e_mark}")
        raise # Re-lanzamos para que Celery maneje el retry de la tarea de reprocess