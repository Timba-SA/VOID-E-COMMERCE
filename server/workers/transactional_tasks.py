# /server/workers/transactional_tasks.py# /server/workers/transactional_tasks.py



import loggingimport logging

import asyncioimport asyncio

from datetime import datetime

from pathlib import Path# Importamos la app de Celery para poder definir tareas

from celery_worker import celery_app

# Importamos la app de Celery para poder definir tareas

from celery_worker import celery_app# Importamos el servicio que SÍ sabe cómo mandar emails

from services import email_service 

# Importamos el servicio que SÍ sabe cómo mandar emails

from services import email_service # Configuración del logger

logger = logging.getLogger(__name__)

# Configuración del logger

logger = logging.getLogger(__name__)# --- ¡ACÁ NACE LA MAGIA! ---

# Definimos nuestra nueva tarea de Celery

# --- TAREA DE CONFIRMACIÓN DE COMPRA ---@celery_app.task(

@celery_app.task(    name='tasks.enviar_email_confirmacion_compra',

    name='tasks.enviar_email_confirmacion_compra',    autoretry_for=(Exception,),

    autoretry_for=(Exception,),    retry_kwargs={'max_retries': 5, 'countdown': 60},

    retry_kwargs={'max_retries': 3, 'countdown': 60},    retry_backoff=True

    retry_backoff=True)

)def enviar_email_confirmacion_compra_task(destinatario_email: str, nombre_usuario: str, detalles_orden: dict):

def enviar_email_confirmacion_compra_task(order_id: int):    """

    """    Tarea de Celery para enviar un email de confirmación de compra.

    Tarea de Celery para enviar un email de confirmación de compra.    Se ejecuta en segundo plano para no demorar la respuesta al usuario.

    Se ejecuta en segundo plano para no demorar la respuesta al usuario.    """

        logger.info(f"Iniciando tarea de envío de email de confirmación para {destinatario_email}.")

    Args:    

        order_id: ID de la orden en la base de datos    try:

    """        # 1. Armamos el asunto y el cuerpo del mail

    logger.info(f"📧 Iniciando tarea de envío de email de confirmación para orden #{order_id}")        asunto = f"¡Gracias por tu compra, {nombre_usuario}!"

    

    try:        cuerpo = f"""

        # Ejecutar la función async en el worker de CeleryHola {nombre_usuario},

        try:

            asyncio.run(_send_purchase_confirmation_email(order_id))¡Tu orden ha sido confirmada con éxito!

        except RuntimeError:

            # Si asyncio.run falla (loop ya existe), crear uno nuevoDetalles de tu compra:

            loop = asyncio.new_event_loop()- ID de Orden: {detalles_orden.get('id', 'N/A')}

            asyncio.set_event_loop(loop)- Total: ${detalles_orden.get('total', 0)}

            loop.run_until_complete(_send_purchase_confirmation_email(order_id))- Cantidad de productos: {len(detalles_orden.get('productos', []))}

        

        logger.info(f"✅ Email de confirmación enviado exitosamente para orden #{order_id}")Gracias por confiar en nosotros.

        return f"Email enviado para orden #{order_id}"

El equipo de VOID E-COMMERCE

    except Exception as e:"""

        logger.error(f"❌ Error al enviar email de confirmación para orden #{order_id}: {e}", exc_info=True)

        raise        # 2. `email_service.send_plain_email` es async; ejecutarla desde la tarea Celery

        # usando asyncio.run para que se ejecute correctamente en el worker.

        try:

async def _send_purchase_confirmation_email(order_id: int):            asyncio.run(email_service.send_plain_email(destinatario_email, asunto, cuerpo))

    """        except Exception:

    Función async interna que obtiene los datos de la orden y envía el email.            # Si asyncio.run falla, intentamos crear y usar un loop de forma manual.

    """            import asyncio as _asyncio

    from database.database import get_db_async            loop = _asyncio.new_event_loop()

    from database.models import Orden, DetalleOrden, Usuario, VarianteProducto, Producto            _asyncio.set_event_loop(loop)

    from sqlalchemy import select            loop.run_until_complete(email_service.send_plain_email(destinatario_email, asunto, cuerpo))

    from sqlalchemy.orm import joinedload

            logger.info(f"Email de confirmación enviado exitosamente a {destinatario_email}.")

    # Obtener sesión de DB        return f"Email enviado a {destinatario_email}"

    async for db in get_db_async():

        try:    except Exception as e:

            # Consultar la orden con todos sus detalles        logger.error(f"Error al enviar email de confirmación a {destinatario_email}: {e}", exc_info=True)

            result = await db.execute(        # Re-lanzamos para que Celery registre el fallo y pueda reintentar según configuración

                select(Orden)        raise
                .options(
                    joinedload(Orden.usuario),
                    joinedload(Orden.detalles)
                    .joinedload(DetalleOrden.variante_producto)
                    .joinedload(VarianteProducto.producto)
                )
                .where(Orden.id == order_id)
            )
            order = result.scalars().unique().first()
            
            if not order:
                logger.error(f"❌ Orden #{order_id} no encontrada en la base de datos")
                return
            
            if not order.usuario or not order.usuario.email:
                logger.error(f"❌ Orden #{order_id} no tiene usuario o email asociado")
                return
            
            # Preparar datos para el template
            destinatario_email = order.usuario.email
            nombre_usuario = order.usuario.nombre or "Cliente"
            
            # Generar HTML de productos
            products_html = ""
            for detalle in order.detalles:
                producto = detalle.variante_producto.producto
                variante = detalle.variante_producto
                
                # Obtener primera imagen del producto
                imagen_url = ""
                if producto.imagenes and len(producto.imagenes) > 0:
                    imagen_url = producto.imagenes[0]
                else:
                    # Imagen placeholder si no hay imagen
                    imagen_url = "https://via.placeholder.com/100x100?text=VOID"
                
                # Calcular subtotal
                subtotal = detalle.cantidad * detalle.precio_en_momento_compra
                
                products_html += f"""
                <div class="product-item">
                    <img src="{imagen_url}" alt="{producto.nombre}" class="product-image" onerror="this.src='https://via.placeholder.com/100x100?text=VOID'">
                    <div class="product-details">
                        <div class="product-name">{producto.nombre}</div>
                        <div class="product-variant">Talla: {variante.tamanio} | Color: {variante.color}</div>
                        <div class="product-quantity">Cantidad: {detalle.cantidad} x ${detalle.precio_en_momento_compra:,.2f}</div>
                        <div class="product-price">${subtotal:,.2f}</div>
                    </div>
                </div>
                """
            
            # Leer el template HTML
            template_path = Path(__file__).parent / "email_templates" / "purchase_confirmation.html"
            with open(template_path, 'r', encoding='utf-8') as f:
                html_template = f.read()
            
            # Formatear fecha
            fecha_orden = order.creado_en.strftime("%d/%m/%Y %H:%M") if order.creado_en else datetime.now().strftime("%d/%m/%Y %H:%M")
            
            # Reemplazar placeholders en el template
            html_content = html_template.replace("{ORDER_ID}", str(order.id))
            html_content = html_content.replace("{ORDER_DATE}", fecha_orden)
            html_content = html_content.replace("{PAYMENT_METHOD}", order.metodo_pago or "Mercado Pago")
            html_content = html_content.replace("{PRODUCTS_LIST}", products_html)
            html_content = html_content.replace("{TOTAL_AMOUNT}", f"{order.monto_total:,.2f}")
            
            # Asunto del email
            asunto = f"✅ Confirmación de Compra - Orden #{order.id} - VOID"
            
            # Enviar email usando el servicio de email
            await email_service.send_html_email(
                destinatario=destinatario_email,
                asunto=asunto,
                html_content=html_content
            )
            
            logger.info(f"📬 Email enviado a {destinatario_email} para orden #{order_id}")
            
        except Exception as e:
            logger.error(f"💥 Error al procesar email para orden #{order_id}: {e}", exc_info=True)
            raise
        finally:
            break  # Solo necesitamos una iteración del async generator
