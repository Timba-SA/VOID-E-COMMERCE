# En backend/services/email_service.py

import ssl
import asyncio
import aiosmtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from settings import settings

# --- Configuración de logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!! ARREGLO A LO BESTIA PORQUE DOCKER NO LEE EL .ENV !!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
EMAIL_SENDER = settings.EMAIL_SENDER
EMAIL_PASSWORD = settings.EMAIL_APP_PASSWORD
FRONTEND_URL = settings.FRONTEND_URL
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# --- Verificación de configuración ---
if not all([EMAIL_SENDER, EMAIL_PASSWORD]):
    logger.critical("¡ERROR FATAL! Las variables de entorno EMAIL_SENDER o EMAIL_APP_PASSWORD no están configuradas. El servicio de email no funcionará.")

async def send_order_confirmation_email(payment_info: dict):
    """
    Construye y envía un email de confirmación de compra de forma asíncrona.
    """
    if not all([EMAIL_SENDER, EMAIL_PASSWORD]):
        logger.error("El servicio de email no está configurado para enviar la confirmación de compra.")
        return

    receiver_email = payment_info["payer"]["email"]
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "¡Gracias por tu compra en VOID!"
    message["From"] = EMAIL_SENDER
    message["To"] = receiver_email

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    text = f"¡Hola! Tu compra ha sido confirmada. El total es de ${payment_info['transaction_amount']}."
    
    html = f"""
    <html>
      <body>
        <div style="font-family: sans-serif; text-align: center; padding: 20px;">
          <h1 style="color: #333;">¡Gracias por tu compra en VOID!</h1>
          <p>Hola,</p>
          <p>Tu compra ha sido procesada exitosamente.</p>
          <p style="font-size: 1.2em; font-weight: bold;">Total: ${payment_info['transaction_amount']}</p>
          <p style="margin-top: 30px; font-size: 0.9em; color: #777;">Recibirás otro email con los detalles del envío pronto.</p>
          <p style="font-weight: bold; margin-top: 20px;">VOID Indumentaria</p>
        </div>
      </body>
    </html>
    """
    
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            start_tls=True,
            username=EMAIL_SENDER,
            password=EMAIL_PASSWORD,
            tls_context=context
        )
        logger.info(f"Email de confirmación enviado a {receiver_email}")
    except Exception as e:
        logger.error(f"Error al enviar email de confirmación a {receiver_email}: {e}", exc_info=True)

async def send_plain_email(receiver_email: str, subject: str, body: str):
    """
    Envía un email de texto plano de forma asíncrona.
    """
    if not all([EMAIL_SENDER, EMAIL_PASSWORD]):
        logger.error(f"El servicio de email no está configurado. No se pudo enviar email a {receiver_email}.")
        return

    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = EMAIL_SENDER
    message["To"] = receiver_email

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            start_tls=True,
            username=EMAIL_SENDER,
            password=EMAIL_PASSWORD,
            tls_context=context
        )
        logger.info(f"Email enviado a {receiver_email} con asunto: {subject}")
    except Exception as e:
        logger.error(f"Error al enviar email a {receiver_email}: {e}", exc_info=True)


async def send_password_reset_email(receiver_email: str, token: str):
    """
    Construye y envía un email para resetear la contraseña.
    """
    if not all([EMAIL_SENDER, EMAIL_PASSWORD]):
        logger.error("El servicio de email no está configurado para enviar el reseteo de contraseña.")
        return

    # Normalizar URL del frontend (eliminar barra final si existe)
    frontend_url = settings.FRONTEND_URL.rstrip('/')
    reset_link = f"{frontend_url}/reset-password/{token}"

    message = MIMEMultipart("alternative")
    message["Subject"] = "Recuperación de Contraseña - VOID"
    message["From"] = EMAIL_SENDER
    message["To"] = receiver_email

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    text = f"""
    Hola,
    Recibimos una solicitud para resetear tu contraseña en VOID.
    Hacé click en el siguiente link para continuar: {reset_link}
    Si no fuiste vos, podés ignorar este email.
    """

    html = f"""
    <html>
      <body style="font-family: sans-serif; padding: 20px;">
        <h2 style="color: #333;">Recuperación de Contraseña</h2>
        <p>Hola,</p>
        <p>Recibimos una solicitud para cambiar tu contraseña en VOID. Hacé click en el botón de abajo para crear una nueva.</p>
        <a href="{reset_link}" style="display: inline-block; padding: 12px 24px; background-color: #000; color: #fff; text-decoration: none; font-weight: bold; margin: 20px 0;">
          CREAR NUEVA CONTRASEÑA
        </a>
        <p style="font-size: 0.9em; color: #777;">Si no solicitaste esto, simplemente ignorá este mensaje.</p>
        <p style="font-weight: bold; margin-top: 20px;">VOID</p>
      </body>
    </html>
    """
    
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            start_tls=True,
            username=EMAIL_SENDER,
            password=EMAIL_PASSWORD,
            tls_context=context
        )
        logger.info(f"Email de reseteo de contraseña enviado a {receiver_email}")
    except Exception as e:
        logger.error(f"Error al enviar email de reseteo a {receiver_email}: {e}", exc_info=True)
        raise