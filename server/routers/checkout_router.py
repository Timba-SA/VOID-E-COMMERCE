# server/routers/checkout_router.py

import mercadopago
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from settings import settings #
from database.database import get_db #
from database.models import Orden, DetalleOrden, VarianteProducto, Producto #
from schemas import checkout_schemas #
from workers.transactional_tasks import enviar_email_confirmacion_compra_task #

router = APIRouter(prefix="/api/checkout", tags=["Checkout"])
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configura Mercado Pago SDK si el token está presente
sdk = settings.MERCADOPAGO_TOKEN and mercadopago.SDK(settings.MERCADOPAGO_TOKEN) #
FRONTEND_URL = settings.FRONTEND_URL #
BACKEND_URL = settings.BACKEND_URL #

# ==============================================================================
# Función save_order_and_update_stock (SIN CAMBIOS RESPECTO A TU ORIGINAL)
# ==============================================================================
async def save_order_and_update_stock(
    db: AsyncSession,
    usuario_id: str,
    monto_total: float,
    payment_id: str,
    items_comprados: list,
    metodo_pago: str,
    payer_email: str, # <-- Agregamos el email aquí por si lo necesitamos loguear
    shipping_address: dict = None
):
    """
    Función transaccional para guardar la orden y actualizar el stock.
    O todo se ejecuta con éxito (COMMIT), o nada se guarda (ROLLBACK).
    Retorna el ID de la nueva orden creada.
    """
    new_order_id = None
    try:
        new_order = Orden( #
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
        new_order_id = new_order.id
        logger.info(f"💾 Orden {new_order_id} creada en memoria. Procesando detalles y stock...")


        for item in items_comprados:
            variante_id_str = item.get("id") or item.get("variante_id")
            if not variante_id_str or not variante_id_str.isdigit() or int(variante_id_str) <= 0:
                 logger.warning(f"Item inválido en webhook para orden {new_order_id}: {item}. Saltando...")
                 continue

            variante_id = int(variante_id_str)
            cantidad_comprada_str = item.get("quantity")
            precio_unitario_str = item.get("unit_price") or item.get("price")

            if not cantidad_comprada_str or not cantidad_comprada_str.isdigit() or int(cantidad_comprada_str) <= 0:
                 logger.warning(f"Item con cantidad inválida para orden {new_order_id}: {item}. Saltando...")
                 continue
            cantidad_comprada = int(cantidad_comprada_str)

            if not precio_unitario_str:
                logger.warning(f"Item sin precio unitario para orden {new_order_id}: {item}. Usando 0.0.")
                precio_unitario = 0.0
            else:
                 try:
                    precio_unitario = float(precio_unitario_str)
                 except ValueError:
                    logger.warning(f"Item con precio inválido para orden {new_order_id}: {item}. Usando 0.0.")
                    precio_unitario = 0.0


            db.add(DetalleOrden( #
                orden_id=new_order.id,
                variante_producto_id=variante_id,
                cantidad=cantidad_comprada,
                precio_en_momento_compra=precio_unitario
            ))

            variante_producto = await db.get(VarianteProducto, variante_id, with_for_update=True) #

            if not variante_producto:
                logger.error(f"CRÍTICO [Orden {new_order_id}]: Variante ID {variante_id} no encontrada.")
                raise Exception(f"Variante de producto ID {variante_id} no encontrada.")

            if variante_producto.cantidad_en_stock < cantidad_comprada:
                logger.error(f"CRÍTICO [Orden {new_order_id}]: Stock insuficiente para variante ID {variante_id}. Stock: {variante_producto.cantidad_en_stock}, Pedido: {cantidad_comprada}")
                raise Exception(f"Stock insuficiente para la variante ID {variante_id}")

            variante_producto.cantidad_en_stock -= cantidad_comprada
            logger.info(f"📉 [Orden {new_order_id}] Stock actualizado para variante ID {variante_id}. Nuevo stock: {variante_producto.cantidad_en_stock}")

        logger.info(f"✅ Detalles y stock actualizados correctamente para Orden {new_order_id}.")
        return new_order_id

    except Exception as e:
        logger.error(f"💥 Error CRÍTICO durante la transacción save_order_and_update_stock (Orden {new_order_id}): {e}", exc_info=True)
        raise e # Re-lanzamos la excepción para que el webhook haga rollback

# ==============================================================================
# Función create_preference (CON LA LÍNEA ARREGLADA)
# ==============================================================================
@router.post("/create-preference", summary="Crea preferencia de pago en Mercado Pago")
async def create_preference(request_data: checkout_schemas.PreferenceRequest, db: AsyncSession = Depends(get_db)): #
    cart = request_data.cart
    address = request_data.shipping_address
    shipping_cost = request_data.shipping_cost

    if not cart.items:
        raise HTTPException(status_code=400, detail="El carrito está vacío.")

    items_for_preference = []
    total_amount_calculated = 0.0 # Calculamos para validar
    for item in cart.items:
        variant = await db.get(VarianteProducto, item.variante_id) #
        if not variant:
             logger.warning(f"Checkout intentado con variante ID {item.variante_id} inexistente.")
             raise HTTPException(status_code=404, detail=f"Producto variante no encontrado (ID: {item.variante_id}).")
        if variant.cantidad_en_stock < item.quantity:
            logger.warning(f"Checkout sin stock para variante {item.variante_id}. Stock: {variant.cantidad_en_stock}, Pedido: {item.quantity}")
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para {item.name}. Disponible: {variant.cantidad_en_stock}.")

        # Validar precio del item del carrito
        try:
            unit_price_float = float(item.price)
            if unit_price_float < 0: raise ValueError("Precio negativo")
        except (ValueError, TypeError):
            logger.error(f"Precio inválido en item del carrito al crear preferencia: {item}")
            raise HTTPException(status_code=400, detail=f"Precio inválido para el producto {item.name}.")

        # --- ¡AQUÍ ESTABA EL ERROR ARREGLADO! ---
        items_for_preference.append({
            "id": str(item.variante_id),
            "title": item.name,
            # Usamos los datos de 'variant' (de la DB) que sí tienen talle y color
            "description": f"Talle: {variant.tamanio}, Color: {variant.color}", # <-- ARREGLADO
            "quantity": item.quantity,
            "unit_price": unit_price_float, # Precio validado
            "currency_id": "ARS"
        })
        total_amount_calculated += item.quantity * unit_price_float

    # Validar costo de envío (igual que tu código original)
    try:
        shipping_cost_float = float(shipping_cost) if shipping_cost is not None else 0.0
        if shipping_cost_float < 0:
            raise ValueError("Costo de envío negativo")
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Costo de envío inválido.")

    # Añadir envío como item (igual que tu código original)
    if shipping_cost_float > 0:
        items_for_preference.append({
            "id": "shipping_cost",
            "title": "Costo de Envío",
            "quantity": 1,
            "unit_price": shipping_cost_float,
            "currency_id": "ARS"
        })
        total_amount_calculated += shipping_cost_float

    # Referencia externa (igual que tu código original)
    external_reference = str(cart.user_id or cart.guest_session_id or "guest")

    # Datos del pagador (igual que tu código original, asegurando string en phone)
    # IMPORTANTE: Asegúrate que el objeto 'address' que llega del frontend TENGA todos estos campos.
    #             Si falta alguno (ej. email), MP podría rechazar la preferencia.
    if not address or not hasattr(address, 'email') or not address.email:
         logger.warning("Intento de crear preferencia sin email en address.")
         # Considera si deberías fallar aquí si el email es obligatorio
         # raise HTTPException(status_code=400, detail="Falta email en la dirección de envío.")

    payer_data = {
        "email": address.email if hasattr(address, 'email') else None, # Tomamos email si existe
        "name": address.firstName if hasattr(address, 'firstName') else None,
        "surname": address.lastName if hasattr(address, 'lastName') else None,
        "phone": {
            "area_code": "",
            "number": str(address.phone) if hasattr(address, 'phone') and address.phone else None
         },
        "address": {
            "street_name": address.streetAddress if hasattr(address, 'streetAddress') else None,
            "zip_code": address.postalCode if hasattr(address, 'postalCode') else None
        }
    }

    # Armado de preference_data (igual que tu código original)
    preference_data = {
        "items": items_for_preference,
        # "shipments": { "cost": shipping_cost_float, "mode": "not_specified" }, # Ya va como item
        "payer": payer_data,
        "back_urls": {
            "success": f"{FRONTEND_URL}/payment/success",
            "failure": f"{FRONTEND_URL}/payment/failure",
            "pending": f"{FRONTEND_URL}/payment/pending",
        },
        # "auto_return": "approved", # Comentado
        "notification_url": f"{BACKEND_URL}/api/checkout/webhook",
        "external_reference": external_reference
    }

    logger.info(f"📦 Creando preferencia MP para {external_reference}. Total: {total_amount_calculated:.2f} ARS")
    # logger.debug(f"Payload MP: {preference_data}")

    # Llamada a MP (igual que tu código original con mejor manejo de errores)
    try:
        if not sdk:
            logger.critical("🚨 MP SDK no configurado en create_preference.")
            raise HTTPException(status_code=503, detail="Servicio de pagos no config.")

        preference_response = sdk.preference().create(preference_data)
        preference = preference_response.get("response")
        status_code = preference_response.get("status")

        if status_code not in [200, 201]:
             error_message = "Error desconocido MP."
             if isinstance(preference, dict) and preference.get("message"):
                 error_message = preference["message"]
             logger.error(f"❌ Error MP ({status_code}) al crear pref: {error_message}. Payload: {preference_data}")
             raise HTTPException(status_code=status_code or 500, detail=f"Error MP: {error_message}")

        if not preference or not preference.get("id"):
            logger.error("❌ Respuesta inválida MP (sin ID): %s", preference_response)
            raise HTTPException(status_code=500, detail="Respuesta inválida MP.")

        logger.info(f"✅ Preferencia MP creada: ID={preference.get('id')}")
        return {"preference_id": preference.get("id"), "init_point": preference.get("init_point")}

    except HTTPException as http_exc:
         raise http_exc
    except Exception as e:
        logger.exception(f"💥 Error INESPERADO al crear pref MP: {e}")
        raise HTTPException(status_code=500, detail="Error inesperado conectando con MP.")


# ==============================================================================
# Endpoint webhook_test (SIN CAMBIOS RESPECTO A TU ORIGINAL)
# ==============================================================================
@router.get("/webhook-test", summary="Endpoint de prueba para verificar que el webhook esté accesible")
async def webhook_test():
    """
    Endpoint de prueba para verificar que el webhook de Mercado Pago puede alcanzar el servidor.
    Accede a: TU_URL_PUBLICA/api/checkout/webhook-test
    """
    logger.info("🧪 Endpoint /webhook-test accedido.")
    current_webhook_url = f"{BACKEND_URL}/api/checkout/webhook"
    return {
        "status": "ok",
        "message": "✅ Servidor online!",
        "configured_backend_url": BACKEND_URL,
        "expected_webhook_url": current_webhook_url,
        "instructions": f"Configura esta URL en MP: {current_webhook_url}"
    }

# ==============================================================================
# Endpoint Webhook (CON LOS CAMBIOS PARA EL MAIL Y MEJOR MANEJO DE ERRORES)
# ==============================================================================
@router.post("/webhook", summary="Receptor de notificaciones de Mercado Pago")
async def mercadopago_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payment_id = None
    try:
        data = await request.json()
        logger.info(f"🔔 Webhook MP: Type={data.get('type')}, Action={data.get('action')}, DataID={data.get('data', {}).get('id')}")

        if data.get("type") == "payment":
            payment_id_str = data.get('data', {}).get('id')
            if not payment_id_str or not payment_id_str.isdigit():
                logger.warning(f"⚠️ Webhook 'payment' sin ID válido. Data: {data}")
                return {"status": "ok", "reason": "Payment ID inválido"}

            payment_id = int(payment_id_str)
            logger.info(f"💳 Procesando notif. para Payment ID: {payment_id}")

            # 1. Evitar duplicados
            existing_order_result = await db.execute(select(Orden).filter(Orden.payment_id_mercadopago == str(payment_id))) #
            if existing_order_result.scalars().first():
                logger.warning(f"⚠️ Pago {payment_id} ya procesado. Ignorando.")
                return {"status": "ok", "reason": "Ya procesado"}

            # 2. Obtener info del pago desde MP API
            if not sdk:
                logger.critical("🚨 MP SDK no inicializado en webhook.")
                raise HTTPException(status_code=503, detail="MP SDK no config.")

            payment_info = None
            try:
                logger.info(f"🔍 Consultando API MP para Payment ID: {payment_id}...")
                payment_info_response = sdk.payment().get(payment_id)
                payment_info = payment_info_response.get("response")
                status_mp = payment_info_response.get("status")

                if status_mp != 200 or not payment_info:
                    logger.error(f"❌ Error API MP ({status_mp}) al obtener Payment {payment_id}. Resp: {payment_info}")
                    raise HTTPException(status_code=502, detail=f"Error API MP al obtener pago {payment_id}")

            except Exception as api_exc:
                 logger.exception(f"💥 Error conectando a API MP para Payment {payment_id}: {api_exc}")
                 raise HTTPException(status_code=502, detail=f"Error conexión API MP para {payment_id}")


            logger.info(f"📋 Info Pago {payment_id} obtenida. Estado MP: {payment_info.get('status')}")
            # Descomentar para debug:
            # logger.info(f"🕵️ DEBUG: payment_info completo para {payment_id}: {payment_info}")

            # 3. Procesar SOLO si está APROBADO
            if payment_info.get("status") == "approved":
                logger.info(f"✅ Pago {payment_id} aprobado. Iniciando proceso de orden...")

                payer_info = payment_info.get("payer", {})
                address_info = payer_info.get("address", {}) # Dirección del pagador
                items_comprados = payment_info.get("additional_info", {}).get("items", [])
                external_reference = payment_info.get("external_reference")
                transaction_amount = payment_info.get("transaction_amount")
                payer_email = payer_info.get("email") # Email es clave

                # Validaciones críticas ANTES de la transacción
                if not external_reference:
                    logger.error(f"❌ CRÍTICO [Pago {payment_id}]: Falta external_reference.")
                    raise HTTPException(status_code=400, detail=f"Falta external_reference para {payment_id}")
                if transaction_amount is None:
                    logger.error(f"❌ CRÍTICO [Pago {payment_id}]: Falta transaction_amount.")
                    raise HTTPException(status_code=400, detail=f"Falta transaction_amount para {payment_id}")
                if not payer_email:
                    logger.error(f"❌ CRÍTICO [Pago {payment_id}]: Falta email del pagador.")
                    raise HTTPException(status_code=400, detail=f"Falta email pagador para {payment_id}")
                # Considera si items vacíos es un error o no
                # if not items_comprados:
                #    logger.warning(f"⚠️ [Pago {payment_id}]: MP no devolvió items.")
                #    raise HTTPException(status_code=400, detail=f"Faltan items para {payment_id}")


                # Datos de envío (usamos payer como fallback)
                shipping_address_to_save = {
                    "firstName": payer_info.get("first_name"),
                    "lastName": payer_info.get("last_name"),
                    "email": payer_email,
                    "phone": payer_info.get("phone", {}).get("number"),
                    "streetAddress": address_info.get("street_name"),
                    "streetNumber": address_info.get("street_number"),
                    "zipCode": address_info.get("zip_code"),
                }

                # --- Inicio Transacción DB ---
                new_order_id = None
                try:
                    logger.info(f"⏩ Iniciando transacción DB para Pago {payment_id}...")
                    new_order_id = await save_order_and_update_stock(
                        db=db,
                        usuario_id=str(external_reference),
                        monto_total=float(transaction_amount),
                        payment_id=str(payment_id), #
                        items_comprados=items_comprados,
                        metodo_pago="Mercado Pago",
                        payer_email=payer_email, # Pasamos el email
                        shipping_address=shipping_address_to_save
                    )
                    await db.commit()
                    logger.info(f"✅ COMMIT exitoso. Orden {new_order_id} guardada (Pago {payment_id}).")

                except Exception as db_exc:
                    logger.error(f"⏪ ROLLBACK DB para Pago {payment_id} debido a: {db_exc}")
                    await db.rollback()
                    raise HTTPException(status_code=500, detail=f"Error DB al procesar orden: {str(db_exc)}")
                # --- Fin Transacción DB ---


                # --- Envío de Email (Post-Commit) ---
                if new_order_id:
                    try:
                        logger.info(f"📧 Intentando enviar email para Orden {new_order_id} (Pago {payment_id})...")
                        # 1. Recuperamos la orden COMPLETA
                        result = await db.execute(
                            select(Orden) #
                            .options(
                                joinedload(Orden.detalles) #
                                .joinedload(DetalleOrden.variante_producto) #
                                .joinedload(VarianteProducto.producto) #
                            )
                            .filter(Orden.id == new_order_id)
                        )
                        orden_completa = result.scalars().first()

                        # 2. Sacamos email (ya validado)
                        email_comprador = payer_email

                        # 3. Sacamos nombre (con Plan B)
                        nombre_comprador = shipping_address_to_save.get("firstName")
                        if not nombre_comprador: nombre_comprador = payer_info.get("first_name")
                        if not nombre_comprador and email_comprador: nombre_comprador = email_comprador.split('@')[0]
                        if not nombre_comprador: nombre_comprador = "Cliente"

                        # 4. Verificamos orden recuperada
                        if not orden_completa:
                            logger.error(f"❌ ¡MUY RARO! No se recuperó Orden {new_order_id} post-commit.")
                        elif not orden_completa.detalles:
                             logger.warning(f"⚠️ Orden {new_order_id} sin detalles al preparar email.")

                        # 5. Llamamos a Celery SI tenemos orden y email
                        if orden_completa and email_comprador:
                            detalles_para_email = []
                            try:
                                for det in orden_completa.detalles:
                                    producto_nombre = "Info no disponible"
                                    variante_info = "Info no disponible"
                                    if det.variante_producto:
                                         variante_info = f"Talle: {det.variante_producto.tamanio}, Color: {det.variante_producto.color}"
                                         if det.variante_producto.producto:
                                              producto_nombre = det.variante_producto.producto.nombre
                                    detalles_para_email.append({
                                        "producto_nombre": producto_nombre,
                                        "variante_info": variante_info,
                                        "cantidad": det.cantidad,
                                        "precio_unitario": float(det.precio_en_momento_compra)
                                    })

                                logger.info(f"📧 Preparando Celery task para {email_comprador} (Orden {new_order_id})...")
                                enviar_email_confirmacion_compra_task.delay( #
                                    email_destinatario=email_comprador,
                                    nombre_usuario=nombre_comprador,
                                    orden_id=orden_completa.id,
                                    detalles_orden=detalles_para_email,
                                    monto_total=float(orden_completa.monto_total)
                                )
                                logger.info(f"✅ Celery task enviada para Orden {new_order_id}.")

                            except Exception as celery_prep_exc:
                                 logger.exception(f"💥 Error al preparar datos para Celery (Orden {new_order_id}): {celery_prep_exc}")
                        else:
                            logger.warning(f"⚠️ No se enviará email para Orden {new_order_id} por falta de datos.")

                    except Exception as email_task_exc:
                        logger.exception(f"💥 Error INESPERADO al despachar tarea email (Orden {new_order_id}): {email_task_exc}")
                        # NO hacemos raise. Orden OK.

            else:
                logger.info(f"ℹ️ Pago {payment_id} estado '{payment_info.get('status')}'. No se procesa.")

        else:
            logger.info(f"ℹ️ Webhook tipo '{data.get('type')}' ignorado.")

        logger.info(f"✅ Webhook procesado/ignorado. Respondiendo 200 OK. (Ref Pago: {payment_id if payment_id else 'N/A'})")
        return {"status": "ok"}

    except HTTPException as http_exc:
        logger.error(f"❌ Error HTTP {http_exc.status_code} en webhook (Pago {payment_id}): {http_exc.detail}")
        # El rollback ya se hizo donde se lanzó
        raise http_exc
    except Exception as e:
        logger.exception(f"💥 Error CATASTRÓFICO en webhook (Pago {payment_id}): {e}")
        try: await db.rollback()
        except Exception as rb_err: logger.error(f"🚨 Fallo rollback tras error catastrófico: {rb_err}")
        raise HTTPException(status_code=500, detail=f"Error interno fatal: {str(e)}")