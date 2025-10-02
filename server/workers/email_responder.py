import asyncio
import email
import logging
import os
import sys
from email.header import decode_header
from email.utils import parseaddr
from dataclasses import dataclass

from dotenv import load_dotenv
import aioimaplib

# --- Agrego ruta raíz del proyecto para importar módulos ---
# Esta parte la dejamos como la tenías, asumiendo que es necesaria para tu estructura.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from services import ia_services, email_service
from database.database import AsyncSessionLocal
from database.models import ConversacionIA # Import acá arriba, como debe ser.

# --- Configuración centralizada y mejorada ---
# Usamos una clase para tener todo más ordenado. ¡Más prolijo!
@dataclass
class Settings:
    load_dotenv()
    IMAP_SERVER: str = os.getenv("IMAP_SERVER", "imap.gmail.com")
    EMAIL_ACCOUNT: str = os.getenv("EMAIL_SENDER")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_APP_PASSWORD")
    POLL_INTERVAL: int = int(os.getenv("EMAIL_POLL_INTERVAL", 120)) # Intervalo configurable

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def decode_subject(header):
    """Decodifica el asunto del email para manejar caracteres especiales."""
    if header is None:
        return ""
    decoded_parts = decode_header(header)
    subject = ""
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            subject += part.decode(charset or 'utf-8', 'ignore')
        else:
            subject += part
    return subject

def get_email_body(msg: email.message.Message) -> str:
    """Extrae el cuerpo de texto plano del email de forma más robusta."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    return part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', 'ignore')
                except Exception:
                    # Si falla, intentamos con utf-8 a la fuerza
                    return part.get_payload(decode=True).decode('utf-8', 'ignore')
    else:
        try:
            return msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', 'ignore')
        except Exception:
            return msg.get_payload(decode=True).decode('utf-8', 'ignore')
    return "" # Si no encontramos nada, devolvemos string vacío


class EmailWorker:
    """
    Una clase para encapsular toda la lógica del worker de emails.
    Así separamos responsabilidades y el código es más limpio.
    """
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client: aioimaplib.IMAP4_SSL | None = None

    async def connect(self):
        """Conecta y loguea al servidor IMAP."""
        logger.info(f"Conectando a {self.settings.IMAP_SERVER}...")
        self.client = aioimaplib.IMAP4_SSL(self.settings.IMAP_SERVER)
        await self.client.wait_hello_from_server()
        await self.client.login(self.settings.EMAIL_ACCOUNT, self.settings.EMAIL_PASSWORD)
        await self.client.select("inbox")
        logger.info("Conexión y login exitosos.")

    async def close(self):
        """Cierra la conexión de forma limpia."""
        if self.client and self.client.is_selected():
            await self.client.close()
        if self.client:
            await self.client.logout()
            logger.info("Desconexión de IMAP exitosa.")

    async def fetch_unread_emails(self) -> list[str]:
        """Busca y devuelve los IDs de los emails no leídos."""
        _, data = await self.client.search("UNSEEN")
        mail_ids = data[0].split()
        if not mail_ids:
            logger.info("No hay emails nuevos.")
            return []
        
        logger.info(f"Se encontraron {len(mail_ids)} emails nuevos.")
        return [mail_id.decode() for mail_id in mail_ids]

    async def process_single_email(self, mail_id: str, db_session):
        """Procesa un único email: lo lee, genera respuesta y contesta."""
        try:
            _, fetch_data = await self.client.fetch(mail_id, "(RFC822)")
            msg = email.message_from_bytes(fetch_data[0][1])

            body = get_email_body(msg)
            sender_email = parseaddr(msg["from"])[1]
            subject = decode_subject(msg["subject"])

            if not body:
                logger.warning(f"Email ID {mail_id} de {sender_email} no tiene cuerpo de texto plano. Omitiendo.")
                await self.client.store(mail_id, '+FLAGS', r'(\Seen)')
                return

            logger.info(f"Procesando email ID {mail_id} de: {sender_email} (Asunto: '{subject}')")

            # --- Lógica de IA ---
            catalog = await ia_services.get_catalog_from_db(db_session)
            system_prompt = ia_services.get_chatbot_system_prompt()

            # La llamada a la IA ya es asíncrona, la llamamos directamente.
            ai_response = await ia_services.get_ia_response(
                system_prompt=system_prompt,
                catalog_context=catalog,
                user_prompt=body # Le pasamos solo el body, más simple. La lógica de crear `ConversacionIA` debería estar dentro del servicio.
            )
            
            # --- Envío de respuesta ---
            logger.info(f"Enviando respuesta generada por IA a {sender_email}...")
            await email_service.send_plain_email(
                sender_email,
                f"Re: {subject}",
                ai_response
            )

            # --- Marcar como leído ---
            await self.client.store(mail_id, '+FLAGS', r'(\Seen)')
            logger.info(f"Email ID {mail_id} marcado como leído.")

        except Exception as e:
            logger.error(f"Error al procesar email ID {mail_id}: {e}", exc_info=True)


    async def run(self):
        """El bucle principal del worker."""
        logger.info("Iniciando worker de emails... Presiona CTRL+C para detener.")
        while True:
            try:
                await self.connect()
                
                unread_ids = await self.fetch_unread_emails()
                if unread_ids:
                    async with AsyncSessionLocal() as db_session:
                        tasks = [self.process_single_email(mail_id, db_session) for mail_id in unread_ids]
                        await asyncio.gather(*tasks) # Procesamos todos los mails en paralelo, ¡más rápido!

                await self.close()

            except aioimaplib.IMAP4.error as e:
                logger.error(f"Error de IMAP (verificá credenciales/config): {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Error en el ciclo principal del worker: {e}", exc_info=True)
            
            logger.info(f"Esperando {self.settings.POLL_INTERVAL} segundos para el próximo chequeo...")
            await asyncio.sleep(self.settings.POLL_INTERVAL)


async def main():
    """Función principal para configurar y correr el worker."""
    settings = Settings()
    if not all([settings.EMAIL_ACCOUNT, settings.EMAIL_PASSWORD]):
        logger.critical("¡ERROR FATAL! Las variables de entorno EMAIL_SENDER o EMAIL_APP_PASSWORD no están configuradas.")
        sys.exit(1)

    worker = EmailWorker(settings)
    try:
        await worker.run()
    except asyncio.CancelledError:
        logger.info("Tarea cancelada. Cerrando conexiones...")
    finally:
        await worker.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Deteniendo el worker de emails por petición del usuario (CTRL+C).")