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
    # Con este bloque, o todo se ejecuta con éxito, o nada se guarda.
    async with db.begin_nested():
        try:
            # Creamos la nueva orden
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
            
            # Usamos flush() para enviar los datos a la DB y obtener el ID de la nueva orden,
            # pero SIN confirmar la transacción todavía.
            await db.flush()

            # Iteramos sobre los items para crear los detalles y actualizar el stock
            for item in items_comprados:
                # Nos aseguramos de manejar ambos posibles nombres de campo para el ID y precio
                variante_id = int(item.get("id") or item.get("variante_id"))
                cantidad_comprada = int(item.get("quantity"))
                precio_unitario = float(item.get("unit_price") or item.get("price"))

                # Creamos el detalle de la orden
                db.add(DetalleOrden(
                    orden_id=new_order.id, 
                    variante_producto_id=variante_id,
                    cantidad=cantidad_comprada, 
                    precio_en_momento_compra=precio_unitario
                ))

                # Buscamos la variante y bloqueamos la fila para evitar que otro proceso la modifique
                # hasta que nuestra transacción termine (esto previene "race conditions").
                result = await db.execute(
                    select(VarianteProducto).where(VarianteProducto.id == variante_id).with_for_update()
                )
                variante_producto = result.scalars().first()
                
                # Chequeo de stock
                if not variante_producto or variante_producto.cantidad_en_stock < cantidad_comprada:
                    # Si lanzamos una excepción aquí, el 'async with db.begin()' hará ROLLBACK de todo.
                    raise Exception(f"Stock insuficiente para la variante ID {variante_id}")
                
                # Restamos el stock
                variante_producto.cantidad_en_stock -= cantidad_comprada
            
            # Si el bucle termina sin errores, el bloque 'async with' hará COMMIT de todo al salir.
            logger.info(f"Orden {new_order.id} pre-procesada y stock actualizado. A la espera del COMMIT.")
            return new_order.id

        except Exception as e:
            # No necesitamos db.rollback() aquí, el 'async with' lo maneja solo.
            logger.error(f"Error CRÍTICO durante la transacción de la orden: {e}. Se activará ROLLBACK.")
            # Relanzamos la excepción para que el webhook sepa que algo falló y el 'async with' haga rollback.
            raise HTTPException(status_code=500, detail=f"Error al procesar la orden: {str(e)}")

# 2. ENDPOINT DE PREFERENCIA ACTUALIZADO
@router.post("/create-preference", summary="Crea preferencia para redirigir a MP")
async def create_preference(request_data: checkout_schemas.PreferenceRequest, db: AsyncSession = Depends(get_db)):
    cart = request_data.cart
    address = request_data.shipping_address

    if not cart.items:
        raise HTTPException(status_code=400, detail="El carrito está vacío.")
    
    items_for_preference = []
    for item in cart.items:
        variant = await db.get(VarianteProducto, item.variante_id)
        if not variant or variant.cantidad_en_stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para el producto.")
        
        items_for_preference.append({
            "id": str(item.variante_id), "title": item.name,
            "quantity": item.quantity, "unit_price": item.price,
            "currency_id": "ARS"
        })

    external_reference = cart.user_id or cart.guest_session_id

    preference_data = {
        "items": items_for_preference,
        "payer": {
            "name": address.firstName,
            "surname": address.lastName,
            "phone": {"number": address.phone},
            "address": {
                "street_name": address.streetAddress,
                "zip_code": address.postalCode
            }
        },
        "back_urls": {"success": f"{settings.FRONTEND_URL}/payment/success"},
        "notification_url": f"{settings.BACKEND_URL}/api/checkout/webhook",
        "external_reference": str(external_reference)
    }
    
    try:
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
        return {"preference_id": preference.get("id"), "init_point": preference.get("init_point")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear preferencia de MP: {e}")

# 3. WEBHOOK ACTUALIZADO
@router.post("/webhook", summary="Receptor de notificaciones de Mercado Pago")
async def mercadopago_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    if data.get("type") == "payment":
        payment_id = data.get("data", {}).get("id")
        if not payment_id: return {"status": "ok"}

        existing_order = await db.execute(select(Orden).filter(Orden.payment_id_mercadopago == str(payment_id)))
        if existing_order.scalars().first():
            return {"status": "ok", "reason": "Ya fue procesado"}

        payment_info_response = sdk.payment().get(payment_id)
        payment_info = payment_info_response["response"]

        if payment_info["status"] == "approved":
            # Extraer la dirección del pagador de la info del pago
            payer_info = payment_info.get("payer", {})
            address_info = payer_info.get("address", {})
            shipping_address_to_save = {
                "firstName": payer_info.get("first_name"),
                "lastName": payer_info.get("last_name"),
                "streetAddress": address_info.get("street_name"),
                "postalCode": address_info.get("zip_code"),
                "phone": payer_info.get("phone", {}).get("number")
            }

            await save_order_and_update_stock(
                db=db, 
                usuario_id=payment_info.get("external_reference"),
                monto_total=payment_info.get("transaction_amount"), 
                payment_id=str(payment_id),
                items_comprados=payment_info.get("additional_info", {}).get("items", []),
                metodo_pago="Mercado Pago",
                shipping_address=shipping_address_to_save # Pasamos la dirección para guardarla
            )
    return {"status": "ok"}
