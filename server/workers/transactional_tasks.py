# /server/workers/transactional_tasks.py

import logging

# Importamos la app de Celery para poder definir tareas
from celery_worker import celery_app

# Importamos el servicio que SÍ sabe cómo mandar emails
from services import email_service 

# Configuración del logger
logger = logging.getLogger(__name__)

# --- ¡ACÁ NACE LA MAGIA! ---
# Definimos nuestra nueva tarea de Celery
@celery_app.task(name='tasks.enviar_email_confirmacion_compra')
def enviar_email_confirmacion_compra_task(destinatario_email: str, nombre_usuario: str, detalles_orden: dict):
    """
    Tarea de Celery para enviar un email de confirmación de compra.
    Se ejecuta en segundo plano para no demorar la respuesta al usuario.
    """
    logger.info(f"Iniciando tarea de envío de email de confirmación para {destinatario_email}.")
    
    try:
        # 1. Armamos el asunto y el cuerpo del mail
        asunto = f"¡Gracias por tu compra, {nombre_usuario}!"
        
        # Podés hacer este cuerpo mucho más lindo con HTML si querés
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

        # 2. Usamos el servicio de email para enviar el correo.
        # Esta función `send_plain_email` ya debería existir en tu `email_service`.
        # Es una función normal, no una tarea de Celery.
        email_service.send_plain_email(
            destinatario=destinatario_email,
            asunto=asunto,
            cuerpo=cuerpo
        )

        logger.info(f"Email de confirmación enviado exitosamente a {destinatario_email}.")
        return f"Email enviado a {destinatario_email}"

    except Exception as e:
        logger.error(f"Error al enviar email de confirmación a {destinatario_email}: {e}", exc_info=True)
        # Podés reintentar la tarea si falla
        raise