from celery import Celery
from settings import settings
import asyncio
import logging

# Configuración de logging para ver qué hace el worker
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 1. Creamos la instancia de Celery.
# Le decimos dónde está nuestro "cartero" (el broker, que es Redis).
# Y dónde puede guardar los resultados de las tareas (el backend, también Redis).
celery_app = Celery(
    "tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Argentina/Buenos_Aires', # Buena práctica para la zona horaria
    enable_utc=True,
)

# ==========================================================
# ¡NUESTRA PRIMERA TAREA ASINCRÓNICA!
# ==========================================================
@celery_app.task(name="enviar_email_confirmacion_compra")
def enviar_email_confirmacion_compra(payment_info: dict):
    """
    Tarea de Celery que se encarga de llamar a nuestro servicio de emails.
    """
    # Como nuestras funciones de email_service son 'async', y las tareas de Celery
    # por defecto son 'sync', usamos asyncio.run() para ejecutar el código asíncrono.
    from services import email_service # Importamos acá adentro para evitar problemas de dependencias.
    
    try:
        logger.info(f"WORKER: Recibida tarea para enviar email a {payment_info.get('payer', {}).get('email')}")
        # La función que ya tenías para enviar mails de confirmación
        asyncio.run(email_service.send_order_confirmation_email(payment_info))
        logger.info("WORKER: Tarea de envío de email completada exitosamente.")
    except Exception as e:
        logger.error(f"WORKER: Falló la tarea de envío de email. Error: {e}", exc_info=True)
        # Celery puede reintentar la tarea si configuramos `bind=True` y `self.retry(exc=e)`,
        # pero por ahora, solo registramos el error.