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

@dataclass
class MockConversationForEmail:
    prompt: str
    respuesta: str | None = None

@dataclass
class Settings:
    load_dotenv()
    IMAP_SERVER: str = os.getenv("IMAP_SERVER", "imap.gmail.com")
    EMAIL_ACCOUNT: str = os.getenv("EMAIL_SENDER")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_APP_PASSWORD")

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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_and_process_emails():
    settings = Settings()
    if not all([settings.EMAIL_ACCOUNT, settings.EMAIL_PASSWORD]):
        logger.error("Email worker: Faltan variables de entorno.")
        return

    client = None
    mailbox_selected = False
    try:
        logger.info(f"Conectando a {settings.IMAP_SERVER}...")
        client = aioimaplib.IMAP4_SSL(settings.IMAP_SERVER)
        await client.wait_hello_from_server()
        await client.login(settings.EMAIL_ACCOUNT, settings.EMAIL_PASSWORD)
        await client.select("inbox")
        mailbox_selected = True
        logger.info("Conexión IMAP exitosa para la tarea Celery.")

        _, data = await client.search("UNSEEN")
        mail_ids = [mail_id.decode() for mail_id in data[0].split()]

        if not mail_ids:
            logger.info("No hay emails nuevos para procesar.")
        else:
            logger.info(f"Se encontraron {len(mail_ids)} emails nuevos.")
            async with AsyncSessionLocal() as db_session:
                for mail_id in mail_ids:
                    try:
                        _, fetch_data = await client.fetch(mail_id, "(RFC822)")
                        
                        # --- CORRECCIÓN 1: Usamos el índice correcto ---
                        msg = email.message_from_bytes(fetch_data[1]) 
                        
                        body = get_email_body(msg)
                        sender = parseaddr(msg["from"])[1]
                        subject = decode_subject(msg["subject"])

                        if not body:
                            logger.warning(f"Email ID {mail_id} de {sender} sin cuerpo. Marcando como leído.")
                            await client.store(mail_id, '+FLAGS', r'(\Seen)')
                            continue

                        logger.info(f"Procesando email de {sender} (Asunto: '{subject}')")
                        
                        user_message = MockConversationForEmail(prompt=body)
                        
                        catalog = await ia_services.get_catalog_from_db(db_session)
                        system_prompt = ia_services.get_chatbot_system_prompt()
                        ai_response = await ia_services.get_ia_response(
                            system_prompt=system_prompt,
                            catalog_context=catalog,
                            chat_history=[user_message]
                        )
                        await email_service.send_plain_email(sender, f"Re: {subject}", ai_response)
                        await client.store(mail_id, '+FLAGS', r'(\Seen)')
                        logger.info(f"Email ID {mail_id} procesado y marcado como leído.")
                    except Exception as e:
                        logger.error(f"Error procesando email ID {mail_id}: {e}", exc_info=True)
    
    except Exception as e:
        logger.error(f"Error en la tarea de procesamiento de emails: {e}", exc_info=True)
    
    finally:
        if client:
            if mailbox_selected:
                await client.close()
            await client.logout()
            logger.info("Desconexión de IMAP completa.")


@celery_app.task(name='tasks.process_unread_emails')
def process_unread_emails_task():
    logger.info("Iniciando la tarea periódica de revisión de emails.")
    asyncio.run(check_and_process_emails())
    logger.info("Tarea periódica de revisión de emails finalizada.")