# /server/workers/email_celery_task.py

import asyncio
import email
import logging
import os
from email.header import decode_header
from email.utils import parseaddr
from dataclasses import dataclass

import aioimaplib
from dotenv import load_dotenv

from celery_worker import celery_app
from services import ia_services, email_service
from database.database import AsyncSessionLocal

# --- Configuración de Settings ---
@dataclass
class Settings:
    load_dotenv()
    IMAP_SERVER: str = os.getenv("IMAP_SERVER", "imap.gmail.com")
    EMAIL_ACCOUNT: str = os.getenv("EMAIL_SENDER")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_APP_PASSWORD")

settings = Settings()

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Funciones de Utilidad para Parsear Emails (sin cambios) ---
def decode_subject(header):
    if header is None: return ""
    subject = ""
    for part, charset in decode_header(header):
        if isinstance(part, bytes): subject += part.decode(charset or 'utf-8', 'ignore')
        else: subject += part
    return subject

def get_email_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition")):
                try: return part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', 'ignore')
                except: return part.get_payload(decode=True).decode('utf-8', 'ignore')
    else:
        try: return msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', 'ignore')
        except: return msg.get_payload(decode=True).decode('utf-8', 'ignore')
    return ""

# --- Lógica de Procesamiento Refactorizada ---

async def process_single_email(client: aioimaplib.IMAP4_SSL, mail_id: str):
    """
    Procesa un único email de forma autónoma.
    Crea y gestiona su propia sesión de base de datos para evitar conflictos de event loop.
    """
    # La sesión de base de datos se crea y se usa exclusivamente dentro de esta tarea.
    async with AsyncSessionLocal() as db_session:
        try:
            # 1. Obtenemos el contenido del email
            _, fetch_data = await client.fetch(mail_id, "(RFC822)")
            msg = email.message_from_bytes(fetch_data[0][1])

            body = get_email_body(msg)
            sender = parseaddr(msg["from"])[1]
            subject = decode_subject(msg["subject"])

            if not body:
                logger.warning(f"Email ID {mail_id} de {sender} sin cuerpo de texto. Marcando como leído.")
                await client.store(mail_id, '+FLAGS', r'(\Seen)')
                return

            logger.info(f"Procesando email de {sender} (Asunto: '{subject}')")
            
            # 2. Obtenemos el contexto necesario usando la sesión de DB local
            catalog = await ia_services.get_catalog_from_db(db_session)
            system_prompt = ia_services.get_chatbot_system_prompt()
            
            # 3. Llamamos al servicio de IA
            ai_response = await ia_services.get_ia_response(
                system_prompt=system_prompt,
                catalog_context=catalog,
                user_prompt=body
            )

            # 4. Enviamos la respuesta y marcamos el email como leído
            await email_service.send_plain_email(sender, f"Re: {subject}", ai_response)
            await client.store(mail_id, '+FLAGS', r'(\Seen)')
            logger.info(f"Email ID {mail_id} procesado y marcado como leído exitosamente.")

        except Exception as e:
            logger.error(f"Falló el procesamiento del email ID {mail_id}: {e}", exc_info=True)


async def check_and_process_emails():
    """
    Función principal que se conecta a IMAP y orquesta el procesamiento en paralelo de los emails.
    Delega la gestión de la sesión de DB a cada tarea individual.
    """
    if not all([settings.EMAIL_ACCOUNT, settings.EMAIL_PASSWORD]):
        logger.error("Email worker: Faltan variables de entorno (EMAIL_SENDER, EMAIL_APP_PASSWORD).")
        return

    client = None
    try:
        logger.info(f"Conectando a {settings.IMAP_SERVER}...")
        client = aioimaplib.IMAP4_SSL(settings.IMAP_SERVER)
        await client.wait_hello_from_server()
        await client.login(settings.EMAIL_ACCOUNT, settings.EMAIL_PASSWORD)
        await client.select("inbox")
        logger.info("Conexión IMAP exitosa para la tarea Celery.")

        _, data = await client.search("UNSEEN")
        mail_ids = [mail_id.decode() for mail_id in data[0].split()]

        if not mail_ids:
            logger.info("No hay emails nuevos para procesar.")
            return
            
        logger.info(f"Se encontraron {len(mail_ids)} emails nuevos. Procesando en paralelo...")
        
        # Creamos una lista de tareas (una por cada email) y las ejecutamos concurrentemente.
        tasks = [process_single_email(client, mail_id) for mail_id in mail_ids]
        await asyncio.gather(*tasks)

    except Exception as e:
        logger.error(f"Error crítico en la tarea de procesamiento de emails: {e}", exc_info=True)
    
    finally:
        if client:
            if client.is_selected():
                await client.close()
            await client.logout()
            logger.info("Desconexión de IMAP completa.")

# --- Tarea de Celery ---

@celery_app.task(name='tasks.process_unread_emails')
def process_unread_emails_task():
    """
    Tarea síncrona de Celery que envuelve y ejecuta la lógica asíncrona.
    """
    logger.info("Iniciando la tarea periódica de revisión de emails.")
    asyncio.run(check_and_process_emails())
    logger.info("Tarea periódica de revisión de emails finalizada.")