# server/routers/checkout_router.py

import mercadopago
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from settings import settings
from database.database import get_db
from database.models import Orden, DetalleOrden, VarianteProducto, Producto
from schemas import checkout_schemas
from workers.transactional_tasks import enviar_email_confirmacion_compra_task

router = APIRouter(prefix="/api/checkout", tags=["Checkout"])
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sdk = settings.MERCADOPAGO_TOKEN and mercadopago.SDK(settings.MERCADOPAGO_TOKEN)
FRONTEND_URL = settings.FRONTEND_URL
BACKEND_URL = settings.BACKEND_URL

async def save_order_and_update_stock(
    db: AsyncSession, 
    usuario_id: str, 
    monto_total: float, 
    payment_id: str, 
    items_comprados: list,
    metodo_pago: str,
    shipping_address: dict = None
):
    """
    Función transaccional para guardar la orden y actualizar el stock.
    O todo se ejecuta con éxito (COMMIT), o nada se guarda (ROLLBACK).
    """
    async with db.begin_nested():
        try:
            new_order = Orden(
                usuario_id=usuario_id, 
                monto_total=monto_total, 
                estado="Completado",
                estado_pago="Aprobado", 
                metodo_pago=metodo_pago,
                payment_id_mercadopago=payment_id,
                direccion_envio=shipping_address
            )
            db.add(new_order)
            await db.flush()

            for item in items_comprados:
                # Nos aseguramos de que el item de envío (si existe) no se procese aquí.
                # Mercado Pago devuelve solo los items que son productos.
                variante_id_str = item.get("id") or item.get("variante_id")
                if not variante_id_str or not variante_id_str.isdigit() or int(variante_id_str) <= 0:
                    continue

                variante_id = int(variante_id_str)
                cantidad_comprada = int(item.get("quantity"))
                precio_unitario = float(item.get("unit_price") or item.get("price"))

                db.add(DetalleOrden(
                    orden_id=new_order.id, 
                    variante_producto_id=variante_id,
                    cantidad=cantidad_comprada, 
                    precio_en_momento_compra=precio_unitario
                ))

                result = await db.execute(
                    select(VarianteProducto).where(VarianteProducto.id == variante_id).with_for_update()
                )
                variante_producto = result.scalars().first()
                
                if not variante_producto or variante_producto.cantidad_en_stock < cantidad_comprada:
                    raise Exception(f"Stock insuficiente para la variante ID {variante_id}")
                
                variante_producto.cantidad_en_stock -= cantidad_comprada
            
            logger.info(f"Orden {new_order.id} pre-procesada y stock actualizado. A la espera del COMMIT.")
            return new_order.id

        except Exception as e:
            logger.error(f"Error CRÍTICO durante la transacción de la orden: {e}. Se activará ROLLBACK.")
            raise HTTPException(status_code=500, detail=f"Error al procesar la orden: {str(e)}")


@router.post("/create-preference", summary="Crea preferencia de pago en Mercado Pago")
async def create_preference(request_data: checkout_schemas.PreferenceRequest, db: AsyncSession = Depends(get_db)):
    cart = request_data.cart
    address = request_data.shipping_address
    shipping_cost = request_data.shipping_cost

    if not cart.items:
        raise HTTPException(status_code=400, detail="El carrito está vacío.")
    
    items_for_preference = []
    for item in cart.items:
        variant = await db.get(VarianteProducto, item.variante_id)
        if not variant or variant.cantidad_en_stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para el producto {item.name}.")
        
        items_for_preference.append({
            "id": str(item.variante_id), "title": item.name,
            "quantity": item.quantity, "unit_price": item.price,
            "currency_id": "ARS"
        })

    external_reference = cart.user_id or cart.guest_session_id

    preference_data = {
        "items": items_for_preference,
        "shipments": { "cost": shipping_cost, "mode": "not_specified" },
        "payer": {
            "name": address.firstName, "surname": address.lastName,
            "phone": {"number": str(address.phone)},
            "address": { "street_name": address.streetAddress, "zip_code": address.postalCode }
        },
        "back_urls": {
            "success": f"{FRONTEND_URL}/payment/success",
            "failure": f"{FRONTEND_URL}/payment/failure",
            "pending": f"{FRONTEND_URL}/payment/pending",
        },
        # --- ¡LÍNEA ELIMINADA PARA DESARROLLO LOCAL! ---
        # "auto_return": "approved", 
        "notification_url": f"{BACKEND_URL}/api/checkout/webhook",
        "external_reference": str(external_reference)
    }
    
    try:
        if not sdk:
            raise HTTPException(status_code=503, detail="El servicio de pagos no está configurado.")
        
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response.get("response")
        
        if not preference or not preference.get("id"):
            logger.error("Error en la respuesta de MP al crear preferencia: %s", preference_response)
            raise HTTPException(status_code=500, detail="Respuesta inválida del servicio de pagos.")
            
        return {"preference_id": preference.get("id"), "init_point": preference.get("init_point")}
        
    except Exception as e:
        logger.error(f"Error general al crear la preferencia de Mercado Pago: %s", e)
        raise HTTPException(status_code=500, detail=f"Error al conectar con Mercado Pago: {e}")


@router.post("/webhook", summary="Receptor de notificaciones de Mercado Pago")
async def mercadopago_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    if data.get("type") == "payment":
        payment_id = data.get("data", {}).get("id")
        if not payment_id: 
            return {"status": "ok"}

        existing_order = await db.execute(select(Orden).filter(Orden.payment_id_mercadopago == str(payment_id)))
        if existing_order.scalars().first():
            logger.warning(f"Intento de procesar pago ya existente: {payment_id}")
            return {"status": "ok", "reason": "Pago ya procesado"}

        payment_info_response = sdk.payment().get(payment_id)
        payment_info = payment_info_response["response"]

        if payment_info.get("status") == "approved":
            payer_info = payment_info.get("payer", {})
            address_info = payer_info.get("address", {})
            shipping_address_to_save = {
                "firstName": payer_info.get("first_name"), "lastName": payer_info.get("last_name"),
                "streetAddress": address_info.get("street_name"), "postalCode": address_info.get("zip_code"),
                "phone": payer_info.get("phone", {}).get("number")
            }

            try:
                await save_order_and_update_stock(
                    db=db, 
                    usuario_id=payment_info.get("external_reference"),
                    monto_total=payment_info.get("transaction_amount"), 
                    payment_id=str(payment_id),
                    items_comprados=payment_info.get("additional_info", {}).get("items", []),
                    metodo_pago="Mercado Pago",
                    shipping_address=shipping_address_to_save
                )
                enviar_email_confirmacion_compra_task.delay(payment_info)
            
            except HTTPException as http_exc:
                logger.error(f"Fallo al procesar el webhook para el pago {payment_id}: {http_exc.detail}")
                raise http_exc

    return {"status": "ok"}