# /server/workers/email_celery_task.py

import asyncio
import logging

from imap_tools import MailBox

# Importamos la configuración central y la app de Celery
from settings import settings
from celery_worker import celery_app

# Importamos los servicios que necesitamos
from services import ia_services, email_service
from database.database import AsyncSessionLocal

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
        # La conexión y login ahora son una sola línea.
        # El 'with' se encarga de conectar, loguear y desconectar automáticamente. ¡Magia!
        with MailBox(settings.IMAP_SERVER).login(settings.EMAIL_SENDER, settings.EMAIL_APP_PASSWORD) as mailbox:
            
            # Buscamos emails no leídos. 'mark_seen=False' para que no los marque como leídos al toque.
            # Convertimos a lista para saber cuántos hay.
            unread_emails = list(mailbox.fetch(criteria="UNSEEN", mark_seen=False))
            
            if not unread_emails:
                logger.info("No hay emails nuevos para procesar.")
                return
                
            logger.info(f"Se encontraron {len(unread_emails)} emails nuevos.")
            
            # Creamos una sesión de DB para usar en todos los emails de esta tanda
            async with AsyncSessionLocal() as db_session:
                for msg in unread_emails:
                    try:
                        logger.info(f"Procesando email de {msg.from_} (Asunto: '{msg.subject}')")

                        # imap-tools ya nos da el cuerpo del texto plano directamente
                        body = msg.text or msg.html

                        if not body:
                            logger.warning(f"Email ID {msg.uid} de {msg.from_} sin cuerpo. Marcando como leído.")
                            mailbox.flag([msg.uid], '\\Seen', True) # Lo marcamos como leído para no volver a procesarlo
                            continue
                        
                        # --- Lógica de IA (no cambia) ---
                        catalog = await ia_services.get_catalog_from_db(db_session)
                        system_prompt = ia_services.get_chatbot_system_prompt()
                        
                        # Armamos un historial simple para la IA
                        # NOTA: Asegurate que tu 'ia_services.get_ia_response' pueda recibir
                        # una lista de diccionarios en el parámetro 'chat_history'.
                        chat_history = [{'role': 'user', 'content': body}]

                        ai_response = await ia_services.get_ia_response(
                            system_prompt=system_prompt,
                            catalog_context=catalog,
                            chat_history=chat_history 
                        )
                        
                        # --- Envío de respuesta (no cambia) ---
                        await email_service.send_plain_email(msg.from_, f"Re: {msg.subject}", ai_response)
                        
                        # Si todo salió bien, AHORA SÍ lo marcamos como leído en el servidor
                        mailbox.flag([msg.uid], '\\Seen', True)
                        logger.info(f"Email ID {msg.uid} procesado y marcado como leído.")
                    
                    except Exception as e:
                        logger.error(f"Error procesando el email ID {msg.uid}: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"Error fatal en la tarea de procesamiento de emails (revisá credenciales o conexión): {e}", exc_info=True)
        # Relanzamos la excepción para que Celery marque la tarea como fallida
        raise


@celery_app.task(name='tasks.process_unread_emails')
def process_unread_emails_task():
    """
    Tarea de Celery que se ejecuta periódicamente para revisar el correo.
    """
    logger.info("Iniciando la tarea periódica de revisión de emails.")
    try:
        # Llamamos a nuestra función asíncrona principal
        asyncio.run(check_and_process_emails())
    except Exception as e:
        logger.critical(f"La tarea 'process_unread_emails_task' falló catastróficamente: {e}")
        # La excepción ya fue registrada en la función de arriba, acá solo la dejamos pasar
        # para que Celery la registre como un fallo.