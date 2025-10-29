# /server/workers/email_celery_task_OPTIMIZED.py

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

# Configuración del logger con formato mejorado y emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] 📧 %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def check_and_process_emails():
    """
    Función OPTIMIZADA con:
    - Dead Letter Queue (max 5 intentos)
    - Logs mejorados con emojis
    - Uso de caché FAQ
    - Catálogo optimizado (máx 2000 chars)
    - Historial reducido (3 turnos vs 5)
    - Sleep reducido (10s vs 30s)
    """
    if not all([settings.EMAIL_SENDER, settings.EMAIL_APP_PASSWORD]):
        logger.error("❌ Email worker: Faltan variables de entorno EMAIL_SENDER o EMAIL_APP_PASSWORD.")
        return

    try:
        logger.info("🔌 Conectando a servidor IMAP...")
        with MailBox(settings.IMAP_SERVER).login(settings.EMAIL_SENDER, settings.EMAIL_APP_PASSWORD) as mailbox:
            # Usamos list() para obtener todos los UIDs antes de empezar a procesar
            unread_emails = list(mailbox.fetch(criteria="UNSEEN", mark_seen=False))

            if not unread_emails:
                logger.info("✅ No hay emails nuevos para procesar.")
                return

            logger.info(f"📬 {len(unread_emails)} emails nuevos encontrados.")

            # Verificamos que la fábrica de sesiones esté inicializada en este proceso
            if database.AsyncSessionLocal is None:
                logger.info("🔧 Inicializando AsyncSessionLocal en worker...")
                database.setup_database_engine()

            # Iteramos sobre los emails obtenidos
            for idx, msg in enumerate(unread_emails, 1):
                email_uid = str(getattr(msg, 'uid', 'unknown_uid'))

                logger.info(f"📧 [{idx}/{len(unread_emails)}] Procesando UID {email_uid}...")

                # --- Abrimos una sesión POR CADA EMAIL ---
                async with database.AsyncSessionLocal() as db_session:
                    email_task_id = None
                    try:
                        # Normalizamos remitente
                        sender = msg.from_values.email if msg.from_values else str(msg.from_)
                        logger.info(f"👤 Remitente: {sender} | Asunto: '{msg.subject or 'Sin asunto'}'")

                        body = msg.text or msg.html or ""

                        if not body:
                            logger.warning(f"⚠️ Email UID {email_uid} sin cuerpo. Marcando como leído.")
                            mailbox.flag([msg.uid], '\\Seen', True)
                            continue

                        # --- Verificar si ya existe este UID en la DB ---
                        existing_task_result = await db_session.execute(
                            select(EmailTask).where(EmailTask.uid == email_uid)
                        )
                        existing_task = existing_task_result.scalar_one_or_none()

                        if existing_task:
                            # Email ya fue procesado antes
                            if existing_task.status == 'done':
                                logger.info(f"✅ UID {email_uid} ya procesado exitosamente. Marcando como leído.")
                                mailbox.flag([msg.uid], '\\Seen', True)
                                continue
                            
                            elif existing_task.status == 'dead_letter':
                                logger.warning(f"💀 UID {email_uid} en DEAD LETTER QUEUE (max intentos alcanzados). Marcando como leído.")
                                mailbox.flag([msg.uid], '\\Seen', True)
                                continue
                            
                            elif existing_task.attempts >= EmailTask.MAX_ATTEMPTS:
                                # Mover a dead letter queue
                                logger.error(f"💀 UID {email_uid} alcanzó MAX_ATTEMPTS ({EmailTask.MAX_ATTEMPTS}). Moviendo a Dead Letter Queue.")
                                await db_session.execute(
                                    update(EmailTask)
                                    .where(EmailTask.id == existing_task.id)
                                    .values(
                                        status='dead_letter',
                                        error_message=f"Max attempts ({EmailTask.MAX_ATTEMPTS}) reached",
                                        procesado_en=datetime.utcnow()
                                    )
                                )
                                await db_session.commit()
                                mailbox.flag([msg.uid], '\\Seen', True)
                                
                                # TODO: Enviar notificación al admin
                                logger.critical(f"🚨 ADMIN ALERT: Email UID {email_uid} movido a Dead Letter Queue")
                                continue
                            
                            else:
                                # Reintentar procesamiento
                                email_task_id = existing_task.id
                                logger.info(f"🔄 UID {email_uid} (Task {email_task_id}) será reintentado. Intento {existing_task.attempts + 1}/{EmailTask.MAX_ATTEMPTS}")
                        else:
                            # Crear nuevo EmailTask
                            email_task = EmailTask(
                                sender_email=sender,
                                subject=msg.subject,
                                body=body,
                                uid=email_uid,
                                status='pending',
                                attempts=0
                            )
                            db_session.add(email_task)
                            await db_session.commit()
                            await db_session.refresh(email_task)
                            email_task_id = email_task.id
                            logger.info(f"📝 EmailTask {email_task_id} creado para UID {email_uid}")

                        # Actualizar a 'processing' y aumentar attempts
                        await db_session.execute(
                            update(EmailTask)
                            .where(EmailTask.id == email_task_id)
                            .values(
                                status='processing',
                                attempts=EmailTask.attempts + 1,
                                last_attempt_at=datetime.utcnow()
                            )
                        )
                        await db_session.commit()
                        logger.info(f"🔄 Task {email_task_id} marcado como 'processing'")

                        # --- Procesamiento con IA (con rate limiting) ---
                        CONTEXT_TURNS_LIMIT = 3  # Reducido de 5 a 3 para ahorrar tokens
                        
                        logger.info(f"📚 Obteniendo historial de conversaciones (últimos {CONTEXT_TURNS_LIMIT} turnos)...")
                        result = await db_session.execute(
                            select(ConversacionIA)
                            .where(ConversacionIA.sesion_id == sender)
                            .order_by(ConversacionIA.creado_en.desc())
                            .limit(CONTEXT_TURNS_LIMIT * 2)
                        )
                        limited_history = result.scalars().all()[::-1]  # Revertir para orden cronológico

                        # Análisis de intención (SIN consumir API de IA)
                        logger.info(f"🎯 Analizando intención del usuario...")
                        intention_analysis = await ia_services.analyze_user_intention(body)
                        logger.info(f"🎯 Intención detectada: {intention_analysis['primary_intention']}")

                        # Catálogo optimizado (solo productos relevantes)
                        logger.info(f"📦 Generando catálogo optimizado...")
                        catalog = await ia_services.get_enhanced_catalog_from_db(db_session, body)

                        # Agregar productos específicos si es búsqueda
                        if intention_analysis["primary_intention"] == "product_search":
                            logger.info(f"🔍 Búsqueda de productos específicos...")
                            search_result = await ia_services.smart_product_search(db_session, body, limit=3)
                            if search_result["products"]:
                                logger.info(f"✅ {len(search_result['products'])} productos encontrados")
                                matched_lines = ["\n--- PRODUCTOS PARA TU CONSULTA ---"]
                                for prod in search_result["products"][:3]:
                                    stock_info = "Sin stock"
                                    if hasattr(prod, 'variantes') and prod.variantes:
                                        total_stock = sum(v.cantidad_en_stock for v in prod.variantes if v.cantidad_en_stock)
                                        if total_stock > 0:
                                            stock_info = f"Stock: {total_stock}"
                                    
                                    category = prod.categoria.nombre if hasattr(prod, 'categoria') and prod.categoria else 'N/A'
                                    matched_lines.append(
                                        f"ID: {prod.id} | {prod.nombre} | {category} | ${prod.precio} | {stock_info}"
                                    )
                                matched_lines.append("---")
                                catalog = "\n".join(matched_lines) + "\n\n" + catalog[:2000]  # Limitar tamaño total

                        # System prompt optimizado
                        user_preferences = ia_services.analyze_user_preferences(limited_history)
                        system_prompt = ia_services.get_enhanced_system_prompt(user_preferences, intention_analysis)

                        ai_response = ""
                        try:
                            # Llamada a IA con rate limiting y caché FAQ
                            logger.info(f"🤖 Llamando a IA (con caché FAQ y rate limiting)...")
                            ai_response = await ia_services.get_ia_response_with_cache(
                                system_prompt=system_prompt,
                                catalog_context=catalog,
                                chat_history=limited_history,
                                user_prompt=f"Email: {body}",
                                max_retries=2  # Solo 2 reintentos para no bloquear demasiado
                            )
                            logger.info(f"✅ Respuesta IA generada exitosamente")
                        except IAServiceError as e_ia:
                            error_msg = str(e_ia)
                            logger.error(f"❌ IA falló para Task {email_task_id}: {error_msg}")
                            
                            # Respuesta de fallback
                            ai_response = (
                                "¡Hola! Gracias por escribirnos a VOID Indumentaria.\n\n"
                                "En este momento estoy procesando muchas consultas y no pude atender la tuya automáticamente. "
                                "Un miembro de nuestro equipo te responderá personalmente lo antes posible.\n\n"
                                "¡Gracias por tu paciencia!\nVOID"
                            )
                            
                            # Guardar error en la DB pero NO marcar como 'failed' todavía
                            await db_session.execute(
                                update(EmailTask)
                                .where(EmailTask.id == email_task_id)
                                .values(
                                    status='pending',  # Volver a pending para reintento
                                    error_message=error_msg[:1000]
                                )
                            )
                            await db_session.commit()
                            
                            # NO marcar email como leído - se reintentará
                            logger.warning(f"⚠️ Task {email_task_id} vuelve a 'pending' para reintento posterior")
                            
                            # Esperar más tiempo antes del siguiente email
                            await asyncio.sleep(60)
                            continue

                        # --- Envío exitoso ---
                        logger.info(f"📤 Enviando email de respuesta a {sender}...")
                        await email_service.send_plain_email(
                            sender,
                            f"Re: {msg.subject or 'Consulta VOID'}",
                            ai_response
                        )

                        # Marcar como 'done'
                        await db_session.execute(
                            update(EmailTask)
                            .where(EmailTask.id == email_task_id)
                            .values(
                                status='done',
                                response=ai_response,
                                procesado_en=datetime.utcnow(),
                                error_message=None  # Limpiar errores previos
                            )
                        )

                        # Guardar conversación
                        conv = ConversacionIA(sesion_id=sender, prompt=body, respuesta=ai_response)
                        db_session.add(conv)
                        await db_session.commit()

                        # Marcar como leído en IMAP
                        mailbox.flag([msg.uid], '\\Seen', True)
                        logger.info(f"✅ Task {email_task_id} completado OK. Email marcado como leído.")

                        # Espera dinámica basada en rate limiting (reducida a 10s)
                        if idx < len(unread_emails):  # No esperar después del último
                            logger.info(f"⏳ Esperando 10s antes del siguiente email...")
                            await asyncio.sleep(10)

                    except Exception as e_email:
                        logger.exception(f"💥 Error procesando UID {email_uid} (Task {email_task_id}): {e_email}")
                        
                        try:
                            await db_session.rollback()
                            
                            if email_task_id:
                                async with database.AsyncSessionLocal() as error_session:
                                    await error_session.execute(
                                        update(EmailTask)
                                        .where(EmailTask.id == email_task_id)
                                        .values(
                                            status='pending',  # Volver a pending para reintento
                                            error_message=f"Processing Error: {str(e_email)[:500]}"
                                        )
                                    )
                                    await error_session.commit()
                                logger.warning(f"⚠️ Task {email_task_id} marcado como 'pending' tras error")
                        except Exception as e_rollback:
                            logger.critical(f"💀 ROLLBACK FAILED para UID {email_uid}: {e_rollback}")
                        
                        # NO marcar como leído - se reintentará
                        await asyncio.sleep(30)

            logger.info(f"🎉 Procesamiento de {len(unread_emails)} emails completado")

    except Exception as e_fatal:
        logger.critical(f"💀 FATAL ERROR en check_and_process_emails: {e_fatal}", exc_info=True)
        raise


@celery_app.task(
    name='tasks.process_unread_emails',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 5, 'countdown': 60},
    retry_backoff=True,
    time_limit=300
)
def process_unread_emails_task():
    """Tarea de Celery que llama a la lógica async."""
    logger.info("🚀 Iniciando tarea periódica de revisión de emails.")
    try:
        asyncio.run(check_and_process_emails())
        logger.info("✅ Tarea periódica de revisión de emails finalizada con éxito.")
    except Exception as e:
        logger.critical(f"❌ La tarea 'process_unread_emails_task' falló gravemente: {e}", exc_info=True)
        raise


@celery_app.task(
    name='tasks.reprocess_email_task',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 30},
    retry_backoff=True,
    time_limit=180
)
def reprocess_email_task(email_task_id: int):
    """Reprocesa un EmailTask específico por ID."""
    logger.info(f"🔄 Iniciando reprocess de EmailTask id={email_task_id}")

    async def _do_reprocess():
        if database.AsyncSessionLocal is None:
            logger.info("🔧 Reprocess: Configurando engine para este worker.")
            database.setup_database_engine()

        async with database.AsyncSessionLocal() as db_session:
            et = await db_session.get(EmailTask, email_task_id)
            if not et:
                logger.error(f"❌ Reprocess: EmailTask id={email_task_id} no encontrado.")
                return

            logger.info(f"📋 Reprocess: EmailTask id={email_task_id} encontrado. Estado actual: {et.status}")

            # Marcamos como 'reprocessing' y aumentamos attempts
            await db_session.execute(
                update(EmailTask)
                .where(EmailTask.id == email_task_id)
                .values(status='reprocessing', attempts=EmailTask.attempts + 1, last_attempt_at=datetime.utcnow())
            )
            await db_session.commit()
            logger.info(f"🔄 Reprocess: EmailTask id={email_task_id} marcado como 'reprocessing'.")

            # --- Lógica de IA (igual que en check_and_process_emails) ---
            sender = et.sender_email
            body = et.body
            CONTEXT_TURNS_LIMIT = 3
            
            res_hist = await db_session.execute(
                select(ConversacionIA)
                .where(ConversacionIA.sesion_id == sender)
                .order_by(ConversacionIA.creado_en.desc())
                .limit(CONTEXT_TURNS_LIMIT * 2)
            )
            limited_history = res_hist.scalars().all()[::-1]

            intention_analysis = await ia_services.analyze_user_intention(body)
            catalog = await ia_services.get_enhanced_catalog_from_db(db_session, body)

            if intention_analysis["primary_intention"] == "product_search":
                search_result = await ia_services.smart_product_search(db_session, body, limit=3)
                if search_result["products"]:
                    matched_lines = ["\n--- PRODUCTOS PARA TU CONSULTA ---"]
                    for prod in search_result["products"][:3]:
                        stock_info = "Sin stock"
                        if hasattr(prod, 'variantes') and prod.variantes:
                            total_stock = sum(v.cantidad_en_stock for v in prod.variantes if v.cantidad_en_stock)
                            if total_stock > 0:
                                stock_info = f"Stock: {total_stock}"
                        category = prod.categoria.nombre if hasattr(prod, 'categoria') and prod.categoria else 'N/A'
                        matched_lines.append(f"ID: {prod.id} | {prod.nombre} | {category} | ${prod.precio} | {stock_info}")
                    matched_lines.append("---")
                    catalog = "\n".join(matched_lines) + "\n\n" + catalog[:2000]

            user_preferences = ia_services.analyze_user_preferences(limited_history)
            system_prompt = ia_services.get_enhanced_system_prompt(user_preferences, intention_analysis)

            ai_response = ""
            try:
                logger.info(f"🤖 Reprocess: Llamando a IA con caché FAQ...")
                ai_response = await ia_services.get_ia_response_with_cache(
                    system_prompt=system_prompt,
                    catalog_context=catalog,
                    chat_history=limited_history,
                    user_prompt=f"Email: {body}",
                    max_retries=2
                )
                logger.info(f"✅ Reprocess: Respuesta IA generada")
            except IAServiceError as e_ia_reprocess:
                logger.error(f"❌ Reprocess: La IA falló para EmailTask id={email_task_id}: {e_ia_reprocess}")
                ai_response = (
                    "¡Hola! Gracias por escribirnos de nuevo. Soy Kara de VOID Indumentaria.\n\n"
                    "Lamento informarte que sigo teniendo problemas para procesar tu consulta anterior automáticamente. "
                    "Ya he alertado al equipo humano para que le dé prioridad a tu caso.\n\n"
                    "Disculpá las molestias.\nVOID Indumentaria"
                )
                await db_session.execute(
                    update(EmailTask)
                    .where(EmailTask.id == email_task_id)
                    .values(
                        status='failed',
                        response=f"IA Reprocess Error: {e_ia_reprocess}",
                        procesado_en=datetime.utcnow(),
                        error_message=str(e_ia_reprocess)[:1000]
                    )
                )
                await db_session.commit()
                logger.warning(f"⚠️ Reprocess: EmailTask id={email_task_id} marcado como 'failed' por error de IA.")
                return

            # --- Envío y finalización OK del reprocess ---
            logger.info(f"📤 Reprocess: Enviando email de respuesta...")
            await email_service.send_plain_email(sender, f"Re: {et.subject or 'Consulta VOID (Reprocesada)'}", ai_response)

            await db_session.execute(
                update(EmailTask)
                .where(EmailTask.id == email_task_id)
                .values(
                    status='done',
                    response=ai_response,
                    procesado_en=datetime.utcnow(),
                    error_message=None
                )
            )

            conv = ConversacionIA(sesion_id=sender, prompt=body, respuesta=ai_response)
            db_session.add(conv)
            await db_session.commit()
            logger.info(f"✅ Reprocess: EmailTask id={email_task_id} completado y marcado como 'done'.")

    try:
        asyncio.run(_do_reprocess())
    except Exception as e:
        logger.exception(f"💥 Error GRANDE reprocessando EmailTask id={email_task_id}: {e}")
        try:
            async def _mark_failed():
                if database.AsyncSessionLocal is None:
                    database.setup_database_engine()
                async with database.AsyncSessionLocal() as error_session:
                    await error_session.execute(
                        update(EmailTask)
                        .where(EmailTask.id == email_task_id)
                        .values(
                            status='failed',
                            response=f"Reprocess Fatal Error: {str(e)[:1000]}",
                            error_message=str(e)[:1000]
                        )
                    )
                    await error_session.commit()
            asyncio.run(_mark_failed())
            logger.warning(f"⚠️ Reprocess: EmailTask id={email_task_id} marcado como 'failed' debido a excepción fatal.")
        except Exception as e_mark:
            logger.critical(f"💀 Reprocess: NO SE PUDO MARCAR COMO FAILED EmailTask id={email_task_id} tras error fatal: {e_mark}")
        raise
