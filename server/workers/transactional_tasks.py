import logging
import asyncio
from datetime import datetime
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from celery_worker import celery_app
from services import email_service
from database.models import Orden, DetalleOrden, VarianteProducto, Producto
from database.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(
    name="tasks.enviar_email_confirmacion_compra",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    retry_backoff=True
)
def enviar_email_confirmacion_compra_task(order_id: int):
    logger.info(f"=" * 80)
    logger.info(f"🚀 TAREA DE EMAIL INICIADA - Orden ID: {order_id}")
    logger.info(f"=" * 80)
    try:
        logger.info(f"📧 Iniciando envio de email de confirmacion para orden {order_id}")
        asyncio.run(_send_purchase_confirmation_email(order_id))
        logger.info(f"✅ Email de confirmacion enviado exitosamente para orden {order_id}")
        logger.info(f"=" * 80)
    except Exception as e:
        logger.error(f"❌ Error al enviar email de confirmacion para orden {order_id}: {e}", exc_info=True)
        logger.error(f"=" * 80)
        raise


async def _send_purchase_confirmation_email(order_id: int):
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Orden)
            .options(
                joinedload(Orden.detalles).joinedload(DetalleOrden.variante_producto).joinedload(VarianteProducto.producto)
            )
            .where(Orden.id == order_id)
        )
        
        result = await session.execute(stmt)
        orden = result.scalar_one_or_none()
        
        if not orden:
            logger.error(f"Orden {order_id} no encontrada")
            return
        
        if not orden.usuario_id:
            logger.error(f"Email de usuario no encontrado para orden {order_id}")
            return
        
        products_html = ""
        for detalle in orden.detalles:
            producto = detalle.variante_producto.producto
            imagen_url = producto.imagenes[0] if producto.imagenes else "https://via.placeholder.com/150"
            
            variante_info = ""
            if detalle.variante_producto.tamanio:
                variante_info += f"Talla: {detalle.variante_producto.tamanio}"
            if detalle.variante_producto.color:
                if variante_info:
                    variante_info += " | "
                variante_info += f"Color: {detalle.variante_producto.color}"
            
            products_html += f"""
            <div style="border-bottom: 1px solid #eee; padding: 15px 0; display: flex; align-items: center;">
                <img src="{imagen_url}" alt="{producto.nombre}" style="width: 80px; height: 80px; object-fit: cover; margin-right: 15px; border-radius: 4px;">
                <div style="flex: 1;">
                    <h3 style="margin: 0 0 5px 0; font-size: 16px; color: #000;">{producto.nombre}</h3>
                    <p style="margin: 0; font-size: 14px; color: #666;">{variante_info}</p>
                    <p style="margin: 5px 0 0 0; font-size: 14px; color: #666;">Cantidad: {detalle.cantidad}</p>
                </div>
                <div style="text-align: right;">
                    <p style="margin: 0; font-size: 16px; font-weight: bold; color: #000;">${detalle.precio_en_momento_compra:.2f}</p>
                </div>
            </div>
            """
        
        template_path = Path(__file__).parent / "email_templates" / "purchase_confirmation.html"
        
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                html_template = f.read()
        except FileNotFoundError:
            logger.error(f"Template no encontrado en {template_path}")
            html_template = "<html><body><h1>Gracias por tu compra</h1><p>Orden #{ORDER_ID}</p>{PRODUCTS_LIST}<p>Total: ${TOTAL_AMOUNT}</p></body></html>"
        
        fecha_orden = orden.creado_en.strftime("%d/%m/%Y %H:%M")
        
        html_content = html_template.replace("{ORDER_ID}", str(orden.id))
        html_content = html_content.replace("{ORDER_DATE}", fecha_orden)
        html_content = html_content.replace("{PAYMENT_METHOD}", orden.metodo_pago or "Mercado Pago")
        html_content = html_content.replace("{PRODUCTS_LIST}", products_html)
        html_content = html_content.replace("{TOTAL_AMOUNT}", f"{orden.monto_total:.2f}")
        html_content = html_content.replace("{CUSTOMER_NAME}", "Cliente")
        
        await email_service.send_html_email(
            destinatario=orden.usuario_id,
            asunto=f"Confirmacion de compra - Orden #{orden.id}",
            html_content=html_content
        )


@celery_app.task(
    name="tasks.enviar_email_reseteo_password",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 30},
    retry_backoff=True
)
def enviar_email_reseteo_password_task(destinatario_email: str, reset_url: str):
    try:
        logger.info(f"Iniciando envio de email de reseteo de password a {destinatario_email}")
        asyncio.run(
            email_service.send_password_reset_email(
                receiver_email=destinatario_email,
                reset_url=reset_url
            )
        )
        logger.info(f"Email de reseteo de password enviado a {destinatario_email}")
    except Exception as e:
        logger.error(f"Error al enviar email de reseteo a {destinatario_email}: {e}", exc_info=True)
        raise
