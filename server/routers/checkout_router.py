# server/routers/checkout_router.py

import mercadopago
import logging
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from settings import settings #
from database.database import get_db #
from database.models import Orden, DetalleOrden, VarianteProducto, Producto #
from schemas import checkout_schemas #
from workers.transactional_tasks import enviar_email_confirmacion_compra_task #
from services.cache_service import get_cache_async, set_cache_async #

router = APIRouter(prefix="/api/checkout", tags=["Checkout"])
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configura Mercado Pago SDK si el token está presente
sdk = settings.MERCADOPAGO_TOKEN and mercadopago.SDK(settings.MERCADOPAGO_TOKEN) #
FRONTEND_URL = settings.FRONTEND_URL #
BACKEND_URL = settings.BACKEND_URL #

# ==============================================================================
# Función save_order_and_update_stock (CON SOPORTE PARA ÓRDENES PENDIENTES)
# ==============================================================================
async def save_order_and_update_stock(
    db: AsyncSession,
    usuario_id: str,
    monto_total: float,
    payment_id: str,
    items_comprados: list,
    metodo_pago: str,
    payer_email: str, # <-- Agregamos el email aquí por si lo necesitamos loguear
    shipping_address: dict = None,
    pending_payment: bool = False  # Nuevo parámetro para indicar si es una orden pendiente
):
    """
    Función transaccional para guardar la orden y actualizar el stock.
    Si pending_payment=True, crea la orden con estado 'Pendiente' SIN descontar stock.
    Si pending_payment=False, procesa la orden normalmente con descuento de stock.
    O todo se ejecuta con éxito (COMMIT), o nada se guarda (ROLLBACK).
    Retorna el ID de la nueva orden creada.
    """
    new_order_id = None
    try:
        # Determinar estados según si es pago pendiente o confirmado
        if pending_payment:
            estado = "Pendiente"
            estado_pago = "Pendiente"
            logger.info(f"📝 Creando orden PENDIENTE (sin descuento de stock)")
        else:
            estado = "Completado"
            estado_pago = "Aprobado"
            logger.info(f"✅ Creando orden COMPLETADA (con descuento de stock)")
        
        new_order = Orden( #
            usuario_id=usuario_id,
            monto_total=monto_total,
            estado=estado,
            estado_pago=estado_pago,
            metodo_pago=metodo_pago,
            payment_id_mercadopago=payment_id,
            direccion_envio=shipping_address
        )
        db.add(new_order)
        await db.flush()
        new_order_id = new_order.id
        logger.info(f"💾 Orden {new_order_id} creada en memoria. Estado: {estado}. Procesando detalles{'...' if not pending_payment else ' (sin stock)...'}")


        for item in items_comprados:
            variante_id_str = item.get("id") or item.get("variante_id")
            if not variante_id_str:
                logger.warning(f"Item sin ID para orden {new_order_id}: {item}. Saltando...")
                continue
            
            # Convertir a string si es necesario para validar
            variante_id_str = str(variante_id_str)
            if not variante_id_str.isdigit() or int(variante_id_str) <= 0:
                logger.warning(f"Item con ID inválido en orden {new_order_id}: {item}. Saltando...")
                continue

            variante_id = int(variante_id_str)
            
            # Obtener cantidad (puede venir como int o string)
            cantidad_comprada_raw = item.get("quantity")
            if cantidad_comprada_raw is None:
                logger.warning(f"Item sin cantidad para orden {new_order_id}: {item}. Saltando...")
                continue
            
            # Convertir a int sin importar el tipo original
            try:
                cantidad_comprada = int(cantidad_comprada_raw)
                if cantidad_comprada <= 0:
                    raise ValueError("Cantidad debe ser positiva")
            except (ValueError, TypeError):
                logger.warning(f"Item con cantidad inválida para orden {new_order_id}: {item}. Saltando...")
                continue

            # Obtener precio unitario (puede venir como float, int o string)
            precio_unitario_raw = item.get("unit_price") or item.get("price")
            if precio_unitario_raw is None:
                logger.warning(f"Item sin precio unitario para orden {new_order_id}: {item}. Usando 0.0.")
                precio_unitario = 0.0
            else:
                try:
                    precio_unitario = float(precio_unitario_raw)
                except (ValueError, TypeError):
                    logger.warning(f"Item con precio inválido para orden {new_order_id}: {item}. Usando 0.0.")
                    precio_unitario = 0.0


            db.add(DetalleOrden( #
                orden_id=new_order.id,
                variante_producto_id=variante_id,
                cantidad=cantidad_comprada,
                precio_en_momento_compra=precio_unitario
            ))

            # SOLO descontar stock si NO es una orden pendiente
            if not pending_payment:
                variante_producto = await db.get(VarianteProducto, variante_id, with_for_update=True) #

                if not variante_producto:
                    logger.error(f"CRÍTICO [Orden {new_order_id}]: Variante ID {variante_id} no encontrada.")
                    raise Exception(f"Variante de producto ID {variante_id} no encontrada.")

                if variante_producto.cantidad_en_stock < cantidad_comprada:
                    logger.error(f"CRÍTICO [Orden {new_order_id}]: Stock insuficiente para variante ID {variante_id}. Stock: {variante_producto.cantidad_en_stock}, Pedido: {cantidad_comprada}")
                    raise Exception(f"Stock insuficiente para la variante ID {variante_id}")

                variante_producto.cantidad_en_stock -= cantidad_comprada
                logger.info(f"📉 [Orden {new_order_id}] Stock actualizado para variante ID {variante_id}. Nuevo stock: {variante_producto.cantidad_en_stock}")
            else:
                # Solo verificar que exista el producto, sin descontar stock
                variante_producto = await db.get(VarianteProducto, variante_id) #
                if not variante_producto:
                    logger.error(f"CRÍTICO [Orden {new_order_id}]: Variante ID {variante_id} no encontrada.")
                    raise Exception(f"Variante de producto ID {variante_id} no encontrada.")
                logger.info(f"✓ [Orden {new_order_id}] Variante ID {variante_id} verificada (stock no descontado)")

        if pending_payment:
            logger.info(f"✅ Orden PENDIENTE {new_order_id} creada correctamente (stock NO descontado).")
        else:
            logger.info(f"✅ Detalles y stock actualizados correctamente para Orden {new_order_id}.")
        
        return new_order_id

    except Exception as e:
        logger.error(f"💥 Error CRÍTICO durante la transacción save_order_and_update_stock (Orden {new_order_id}): {e}", exc_info=True)
        raise e # Re-lanzamos la excepción para que el webhook haga rollback

# ==============================================================================
# Función para descontar stock de una orden pendiente cuando se aprueba el pago
# ==============================================================================
async def update_order_stock_on_approval(db: AsyncSession, order_id: int):
    """
    Descuenta el stock de los productos de una orden cuando el pago es aprobado.
    Debe llamarse desde el webhook cuando el pago está 'approved'.
    """
    try:
        # Obtener los detalles de la orden
        result = await db.execute(
            select(DetalleOrden).filter(DetalleOrden.orden_id == order_id)
        )
        detalles = result.scalars().all()
        
        if not detalles:
            logger.warning(f"⚠️ No se encontraron detalles para la orden {order_id}")
            return
        
        logger.info(f"📦 Descontando stock para orden {order_id} (pago aprobado)")
        
        for detalle in detalles:
            variante_producto = await db.get(VarianteProducto, detalle.variante_producto_id, with_for_update=True)
            
            if not variante_producto:
                logger.error(f"❌ Variante ID {detalle.variante_producto_id} no encontrada para orden {order_id}")
                raise Exception(f"Variante de producto ID {detalle.variante_producto_id} no encontrada.")
            
            if variante_producto.cantidad_en_stock < detalle.cantidad:
                logger.error(f"❌ Stock insuficiente para variante ID {detalle.variante_producto_id}. Stock: {variante_producto.cantidad_en_stock}, Pedido: {detalle.cantidad}")
                raise Exception(f"Stock insuficiente para la variante ID {detalle.variante_producto_id}")
            
            variante_producto.cantidad_en_stock -= detalle.cantidad
            logger.info(f"📉 Stock actualizado para variante ID {detalle.variante_producto_id}. Nuevo stock: {variante_producto.cantidad_en_stock}")
        
        logger.info(f"✅ Stock descontado correctamente para orden {order_id}")
        
    except Exception as e:
        logger.error(f"💥 Error al descontar stock para orden {order_id}: {e}", exc_info=True)
        raise e

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

    # Referencia externa
    external_reference = str(cart.user_id or cart.guest_session_id or "guest")
    
    # --- GUARDAR DATOS EN REDIS PARA EL WEBHOOK ---
    # NO crear la orden ahora - el webhook la creará cuando el pago sea exitoso
    logger.info(f"� Guardando datos del checkout en Redis para {external_reference}...")
    
    # Preparar items para la orden (se usarán en el webhook)
    items_para_orden = []
    for item in cart.items:
        variant = await db.get(VarianteProducto, item.variante_id)
        if not variant:
            raise HTTPException(status_code=404, detail=f"Variante {item.variante_id} no encontrada")
        
        items_para_orden.append({
            "id": str(item.variante_id),
            "title": item.name,
            "quantity": item.quantity,
            "unit_price": float(item.price)
        })
    
    # Preparar dirección de envío
    shipping_address_dict = {
        "firstName": address.firstName if hasattr(address, 'firstName') else None,
        "lastName": address.lastName if hasattr(address, 'lastName') else None,
        "email": address.email if hasattr(address, 'email') else None,
        "streetAddress": address.streetAddress if hasattr(address, 'streetAddress') else None,
        "city": address.city if hasattr(address, 'city') else None,
        "state": address.state if hasattr(address, 'state') else None,
        "postalCode": address.postalCode if hasattr(address, 'postalCode') else None,
        "country": address.country if hasattr(address, 'country') else None,
        "prefix": address.prefix if hasattr(address, 'prefix') else None,
        "phone": address.phone if hasattr(address, 'phone') else None,
        "comments": address.comments if hasattr(address, 'comments') else None,
    }
    
    # Guardar todos los datos del checkout en Redis (1 hora de expiración)
    checkout_data = {
        "usuario_id": external_reference,
        "items": items_para_orden,
        "shipping_address": shipping_address_dict,
        "total_amount": total_amount_calculated,
        "payer_email": address.email if hasattr(address, 'email') else None
    }
    
    checkout_cache_key = f"checkout_data:{external_reference}"
    await set_cache_async(checkout_cache_key, checkout_data, expire_seconds=3600)
    logger.info(f"✅ Datos del checkout guardados en Redis para {external_reference}")

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

    # Armado de preference_data
    preference_data = {
        "items": items_for_preference,
        "payer": payer_data,
        "back_urls": {
            "success": f"{FRONTEND_URL.rstrip('/')}/payment/success",
            "failure": f"{FRONTEND_URL.rstrip('/')}/payment/failure",
            "pending": f"{FRONTEND_URL.rstrip('/')}/payment/pending",
        },
        "notification_url": f"{BACKEND_URL}/api/checkout/webhook",
        "external_reference": external_reference,  # Solo el usuario_id
        "statement_descriptor": "VOID E-COMMERCE",
    }
    
    # Solo agregar auto_return y binary_mode en PRODUCCIÓN (HTTPS)
    # En localhost (HTTP), MP rechaza auto_return con error 400
    if FRONTEND_URL.startswith("https://"):
        preference_data["auto_return"] = "approved"  # Redirección automática en producción
        preference_data["binary_mode"] = True  # Estados binarios (approved/rejected)
        logger.info(f"🔒 HTTPS detectado - auto_return='approved' y binary_mode activados")
    else:
        logger.info(f"🏠 HTTP/localhost detectado - auto_return desactivado (MP requiere HTTPS)")

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
        # Mercado Pago puede enviar datos en el body (JSON) o en query params
        # Intentar leer del body primero
        data = {}
        try:
            data = await request.json()
        except:
            # Si falla, no hay JSON en el body
            pass
        
        # También leer los query parameters
        query_params = dict(request.query_params)
        
        # Determinar el tipo de notificación
        notification_type = data.get('type') or query_params.get('topic')
        notification_id = data.get('data', {}).get('id') or query_params.get('id') or query_params.get('data.id')
        
        logger.info(f"🔔 Webhook MP: Type={notification_type}, DataID={notification_id}, QueryParams={query_params}")

        if notification_type == "payment":
            payment_id_str = notification_id
            if not payment_id_str or not str(payment_id_str).isdigit():
                logger.warning(f"⚠️ Webhook 'payment' sin ID válido. Data: {data}, Params: {query_params}")
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
                logger.info(f"✅ Pago {payment_id} aprobado. Creando orden...")

                external_reference = payment_info.get("external_reference")
                transaction_amount = payment_info.get("transaction_amount")

                # Validaciones críticas
                if not external_reference:
                    logger.error(f"❌ CRÍTICO [Pago {payment_id}]: Falta external_reference.")
                    raise HTTPException(status_code=400, detail=f"Falta external_reference para {payment_id}")
                if transaction_amount is None:
                    logger.error(f"❌ CRÍTICO [Pago {payment_id}]: Falta transaction_amount.")
                    raise HTTPException(status_code=400, detail=f"Falta transaction_amount para {payment_id}")

                # Obtener datos del checkout desde Redis
                checkout_cache_key = f"checkout_data:{external_reference}"
                checkout_data = await get_cache_async(checkout_cache_key)
                
                if not checkout_data:
                    logger.error(f"❌ No se encontraron datos del checkout para {external_reference}")
                    raise HTTPException(status_code=404, detail="Datos del checkout no encontrados")
                
                logger.info(f"� Datos del checkout recuperados desde Redis para {external_reference}")

                # Crear la orden con estado "Completado" Y descontar stock
                try:
                    new_order_id = await save_order_and_update_stock(
                        db=db,
                        usuario_id=checkout_data.get("usuario_id"),
                        monto_total=transaction_amount,  # Usar monto real de MP
                        payment_id=str(payment_id),
                        items_comprados=checkout_data.get("items"),
                        metodo_pago="Mercado Pago",
                        payer_email=checkout_data.get("payer_email"),
                        shipping_address=checkout_data.get("shipping_address"),
                        pending_payment=False  # Crear orden completada Y descontar stock
                    )
                    
                    await db.commit()
                    logger.info(f"✅ Orden {new_order_id} creada exitosamente con Payment ID {payment_id} y stock descontado")
                    
                    # Limpiar datos del checkout de Redis
                    await set_cache_async(checkout_cache_key, None, expire_seconds=1)
                    logger.info(f"🧹 Datos del checkout eliminados de Redis para {external_reference}")
                    
                    # Opcional: Enviar email de confirmación
                    # TODO: Implementar envío de email aquí si es necesario
                    
                except Exception as e:
                    await db.rollback()
                    logger.error(f"❌ Error al crear orden para pago {payment_id}: {e}")
                    raise HTTPException(status_code=500, detail="Error al crear orden")

                return {"status": "ok", "order_id": new_order_id, "message": f"Orden {new_order_id} creada correctamente"}

            else:
                logger.info(f"ℹ️ Pago {payment_id} estado '{payment_info.get('status')}'. No se procesa.")

        else:
            logger.info(f"ℹ️ Webhook tipo '{notification_type}' ignorado.")

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