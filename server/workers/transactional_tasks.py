# /server/workers/transactional_tasks.py

import logging
import asyncio

# Importamos la app de Celery para poder definir tareas
from celery_worker import celery_app

# Importamos el servicio que SÍ sabe cómo mandar emails
from services import email_service 

# Configuración del logger
logger = logging.getLogger(__name__)

# --- ¡ACÁ NACE LA MAGIA! ---
# Definimos nuestra nueva tarea de Celery
@celery_app.task(
    name='tasks.enviar_email_confirmacion_compra',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 5, 'countdown': 60},
    retry_backoff=True
)
def enviar_email_confirmacion_compra_task(destinatario_email: str, nombre_usuario: str, detalles_orden: dict):
    """
    Tarea de Celery para enviar un email de confirmación de compra.
    Se ejecuta en segundo plano para no demorar la respuesta al usuario.
    """
    logger.info(f"Iniciando tarea de envío de email de confirmación para {destinatario_email}.")
    
    try:
        # 1. Armamos el asunto y el cuerpo del mail
        asunto = f"¡Gracias por tu compra, {nombre_usuario}!"

        cuerpo = f"""
Hola {nombre_usuario},

¡Tu orden ha sido confirmada con éxito!

Detalles de tu compra:
- ID de Orden: {detalles_orden.get('id', 'N/A')}
- Total: ${detalles_orden.get('total', 0)}
- Cantidad de productos: {len(detalles_orden.get('productos', []))}

Gracias por confiar en nosotros.

El equipo de VOID E-COMMERCE
"""

        # 2. `email_service.send_plain_email` es async; ejecutarla desde la tarea Celery
        # usando asyncio.run para que se ejecute correctamente en el worker.
        try:
            asyncio.run(email_service.send_plain_email(destinatario_email, asunto, cuerpo))
        except Exception:
            # Si asyncio.run falla, intentamos crear y usar un loop de forma manual.
            import asyncio as _asyncio
            loop = _asyncio.new_event_loop()
            _asyncio.set_event_loop(loop)
            loop.run_until_complete(email_service.send_plain_email(destinatario_email, asunto, cuerpo))

        logger.info(f"Email de confirmación enviado exitosamente a {destinatario_email}.")
        return f"Email enviado a {destinatario_email}"

    except Exception as e:
        logger.error(f"Error al enviar email de confirmación a {destinatario_email}: {e}", exc_info=True)
        # Re-lanzamos para que Celery registre el fallo y pueda reintentar según configuración
        raise