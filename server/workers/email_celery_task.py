# /server/workers/email_celery_task.py

import asyncio
import logging

from imap_tools import MailBox

# Importamos la configuración central y la app de Celery
from settings import settings
from celery_worker import celery_app

# Importamos los servicios que necesitamos
from services import ia_services, email_service
from services.ia_services import IAServiceError
from database import database
from database.models import EmailTask
from database.models import ConversacionIA
from sqlalchemy import select, update
from datetime import datetime

# Configuración del logger (sin cambios)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def check_and_process_emails():
    """
    Función principal reescrita con imap-tools para ser más confiable.
    Se conecta, busca emails no leídos, los procesa con la IA y responde.
    """
    if not all([settings.EMAIL_SENDER, settings.EMAIL_APP_PASSWORD]):
        logger.error("Email worker: Faltan variables de entorno EMAIL_SENDER o EMAIL_APP_PASSWORD.")
        return

    try:
        # Conexión IMAP
        with MailBox(settings.IMAP_SERVER).login(settings.EMAIL_SENDER, settings.EMAIL_APP_PASSWORD) as mailbox:
            unread_emails = list(mailbox.fetch(criteria="UNSEEN", mark_seen=False))

            if not unread_emails:
                logger.info("No hay emails nuevos para procesar.")
                return

            logger.info(f"Se encontraron {len(unread_emails)} emails nuevos.")

            # Verificamos que la fábrica de sesiones esté inicializada en este proceso
            if database.AsyncSessionLocal is None:
                logger.critical("AsyncSessionLocal no está inicializado en el proceso worker. Llamando a setup_database_engine().")
                database.setup_database_engine()

            async with database.AsyncSessionLocal() as db_session:
                for msg in unread_emails:
                    try:
                        # Normalizamos remitente: imap-tools puede devolver una tupla o string
                        sender = None
                        try:
                            sender = msg.from_[0].addr if isinstance(msg.from_, tuple) else str(msg.from_)
                        except Exception:
                            sender = str(msg.from_)

                        logger.info(f"Procesando email de {sender} (Asunto: '{msg.subject}')")

                        body = (msg.text or "")
                        if not body and msg.html:
                            # Si sólo hay html, intentamos obtener texto plano mínimo
                            body = msg.html

                        if not body:
                            logger.warning(f"Email UID {getattr(msg, 'uid', 'unknown')} sin cuerpo. Marcando como leído.")
                            mailbox.flag([msg.uid], '\\Seen', True)
                            continue

                        # --- Persistimos el email como EmailTask (estado pending) ---
                        email_task = EmailTask(
                            sender_email=sender,
                            subject=msg.subject,
                            body=body,
                            uid=str(getattr(msg, 'uid', '')),
                            status='pending',
                            attempts=0
                        )
                        db_session.add(email_task)
                        await db_session.commit()
                        await db_session.refresh(email_task)
                        logger.info(f"EmailTask creado en DB con id={email_task.id} para UID {email_task.uid}")

                        # Marcamos como processing y aumentamos attempts
                        await db_session.execute(
                            update(EmailTask).where(EmailTask.id == email_task.id).values(status='processing', attempts=EmailTask.attempts + 1)
                        )
                        await db_session.commit()

                        # --- Lógica de IA mejorada (usar mismo flujo que el chatbot mejorado) ---
                        # Recuperamos historial de la conversación por sesion_id (usamos el email del
                        # remitente como sesion_id) y limitamos los turns igual que en el router.
                        CONTEXT_TURNS_LIMIT = 5
                        result = await db_session.execute(
                            select(ConversacionIA).where(ConversacionIA.sesion_id == sender).order_by(ConversacionIA.creado_en)
                        )
                        full_db_history = result.scalars().all()
                        limited_history = full_db_history[-(CONTEXT_TURNS_LIMIT * 2):]

                        # Análisis avanzado de la consulta del email
                        intention_analysis = await ia_services.analyze_user_intention(body)
                        logger.info(f"Intención detectada en email: {intention_analysis['primary_intention']}")

                        # Obtener catálogo optimizado para la consulta específica del email
                        catalog = await ia_services.get_enhanced_catalog_from_db(db_session, body)
                        
                        # Si es una búsqueda de productos, usar búsqueda inteligente
                        if intention_analysis["primary_intention"] == "product_search":
                            search_result = await ia_services.smart_product_search(db_session, body, limit=4)
                            if search_result["products"]:
                                matched_lines = ["\n--- PRODUCTOS ESPECÍFICOS PARA TU CONSULTA ---"]
                                for prod in search_result["products"]:
                                    stock_info = "Sin stock"
                                    if hasattr(prod, 'variantes') and prod.variantes:
                                        total_stock = sum(v.cantidad_en_stock for v in prod.variantes)
                                        if total_stock > 0:
                                            available_sizes = [v.tamanio for v in prod.variantes if v.cantidad_en_stock > 0]
                                            stock_info = f"Stock: {total_stock}"
                                            if available_sizes:
                                                stock_info += f" | Talles: {', '.join(set(available_sizes))}"
                                    
                                    category = prod.categoria.nombre if getattr(prod, 'categoria', None) else 'Sin categoría'
                                    matched_lines.append(
                                        f"🎯 ID: {prod.id} | {prod.nombre} | Categoría: {category} | "
                                        f"Color: {prod.color or 'N/A'} | ${prod.precio} | {stock_info}"
                                    )
                                matched_lines.append("--- FIN PRODUCTOS ESPECÍFICOS ---")
                                catalog = "\n".join(matched_lines) + "\n" + catalog

                        # Generar recomendaciones personalizadas para emails
                        recommendations = await ia_services.get_personalized_recommendations(db_session, sender, limit=3)
                        if recommendations:
                            rec_lines = ["\n--- PRODUCTOS RECOMENDADOS PARA VOS ---"]
                            for rec in recommendations:
                                stock_info = "Sin stock"
                                if hasattr(rec, 'variantes') and rec.variantes:
                                    total_stock = sum(v.cantidad_en_stock for v in rec.variantes)
                                    if total_stock > 0:
                                        available_sizes = [v.tamanio for v in rec.variantes if v.cantidad_en_stock > 0]
                                        stock_info = f"Stock: {total_stock}"
                                        if available_sizes:
                                            stock_info += f" | Talles: {', '.join(set(available_sizes))}"
                                
                                rec_lines.append(
                                    f"⭐ ID: {rec.id} | {rec.nombre} | ${rec.precio} | {stock_info}"
                                )
                            rec_lines.append("--- FIN RECOMENDACIONES ---")
                            catalog += "\n".join(rec_lines)

                        # Generar prompt personalizado para emails
                        user_preferences = ia_services.analyze_user_preferences(limited_history)
                        system_prompt = ia_services.get_enhanced_system_prompt(user_preferences, intention_analysis)

                        try:
                            # Usar IA mejorada con contexto completo
                            ai_response = await ia_services.get_ia_response(
                                system_prompt=system_prompt,
                                catalog_context=catalog,
                                chat_history=limited_history,
                                user_prompt=f"Email recibido: {body}"
                            )
                        except IAServiceError as e:
                            logger.error(f"La IA devolvió un error para el EmailTask id={email_task.id}: {e}")
                            ai_response = (
                                "¡Hola! Gracias por tu mensaje. Soy Kara de VOID Indumentaria. "
                                "En este momento no puedo procesar tu consulta automáticamente, "
                                "pero nuestro equipo te va a responder pronto con toda la info que necesites. "
                                "¡Saludos!"
                            )

                        # --- Envío de respuesta ---
                        await email_service.send_plain_email(sender, f"Re: {msg.subject or ''}", ai_response)

                        # Guardamos la respuesta y marcamos done
                        await db_session.execute(
                            update(EmailTask).where(EmailTask.id == email_task.id).values(status='done', response=ai_response, procesado_en=datetime.utcnow())
                        )
                        await db_session.commit()

                        # Guardamos la conversación en la tabla ConversacionIA (como hace el chatbot)
                        try:
                            conv = ConversacionIA(sesion_id=sender, prompt=body, respuesta=ai_response)
                            db_session.add(conv)
                            await db_session.commit()
                        except Exception:
                            logger.exception("No se pudo guardar la ConversacionIA para auditoría.")

                        mailbox.flag([msg.uid], '\\Seen', True)
                        logger.info(f"EmailTask id={email_task.id} procesado y email UID {getattr(msg, 'uid', 'unknown')} marcado como leído.")

                        # Esperamos 30 segundos para respetar límites de la API antes de procesar el siguiente email
                        logger.info("Esperando 30 segundos antes de procesar el siguiente email para respetar límites de la API.")
                        await asyncio.sleep(30)

                    except Exception as e:
                        logger.exception(f"Error procesando el email UID {getattr(msg, 'uid', 'unknown')}: {e}")

    except Exception as e:
        logger.critical(f"Error fatal en la tarea de procesamiento de emails (revisá credenciales o conexión): {e}", exc_info=True)
        raise


@celery_app.task(name='tasks.process_unread_emails', autoretry_for=(Exception,), retry_kwargs={'max_retries': 10, 'countdown': 30}, retry_backoff=True)
def process_unread_emails_task():
    """
    Tarea de Celery que se ejecuta periódicamente para revisar el correo.
    """
    logger.info("Iniciando la tarea periódica de revisión de emails.")
    try:
        # Llamamos a nuestra función asíncrona principal
        asyncio.run(check_and_process_emails())
    except Exception as e:
        logger.critical(f"La tarea 'process_unread_emails_task' falló catastróficamente: {e}", exc_info=True)
        # Re-levantar la excepción para que Celery haga el retry automático
        raise



@celery_app.task(name='tasks.reprocess_email_task')
def reprocess_email_task(email_task_id: int):
    """
    Reprocesa un EmailTask por id: vuelve a ejecutar la IA y reenvía la respuesta.
    Útil para reintentos manuales desde la DB/admin.
    """
    logger.info(f"Iniciando reprocess de EmailTask id={email_task_id}")
    try:
        # Ejecutamos la lógica de procesamiento usando el loop async
        async def _do():
            if database.AsyncSessionLocal is None:
                database.setup_database_engine()
            async with database.AsyncSessionLocal() as db_session:
                res = await db_session.execute(select(EmailTask).where(EmailTask.id == email_task_id))
                et = res.scalars().first()
                if not et:
                    logger.error(f"EmailTask id={email_task_id} no encontrado")
                    return

                # Reproceso reutilizando el historial con IA mejorada
                CONTEXT_TURNS_LIMIT = 5
                res_hist = await db_session.execute(
                    select(ConversacionIA).where(ConversacionIA.sesion_id == et.sender_email).order_by(ConversacionIA.creado_en)
                )
                full_db_history = res_hist.scalars().all()
                limited_history = full_db_history[-(CONTEXT_TURNS_LIMIT * 2):]

                # Análisis de intención para reprocess
                intention_analysis = await ia_services.analyze_user_intention(et.body)
                
                # Catálogo optimizado
                catalog = await ia_services.get_enhanced_catalog_from_db(db_session, et.body)
                
                # Prompt personalizado para reprocess
                user_preferences = ia_services.analyze_user_preferences(limited_history)
                system_prompt = ia_services.get_enhanced_system_prompt(user_preferences, intention_analysis)

                try:
                    ai_response = await ia_services.get_ia_response(
                        system_prompt=system_prompt, 
                        catalog_context=catalog, 
                        chat_history=limited_history, 
                        user_prompt=f"Email recibido: {et.body}"
                    )
                except IAServiceError:
                    ai_response = (
                        "¡Hola! Gracias por escribirnos. Soy Kara de VOID Indumentaria. "
                        "Tu consulta es importante para nosotros y nuestro equipo te va a responder "
                        "con toda la información que necesités. ¡Saludos!"
                    )

                await email_service.send_plain_email(et.sender_email, f"Re: {et.subject or ''}", ai_response)
                await db_session.execute(update(EmailTask).where(EmailTask.id == et.id).values(status='done', response=ai_response, procesado_en=datetime.utcnow()))
                await db_session.commit()

                # Guardamos la conversación
                try:
                    conv = ConversacionIA(sesion_id=et.sender_email, prompt=et.body, respuesta=ai_response)
                    db_session.add(conv)
                    await db_session.commit()
                except Exception:
                    logger.exception("No se pudo guardar la ConversacionIA al reprocesar el EmailTask.")

        asyncio.run(_do())
    except Exception as e:
        logger.exception(f"Error reprocessando EmailTask id={email_task_id}: {e}")
        raise