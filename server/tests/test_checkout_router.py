# En tests/test_checkout_router.py
import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import Orden, VarianteProducto

# Tests actualizados para el nuevo flujo con orden pendiente pre-preferencia
@pytest.mark.asyncio
async def test_create_preference_creates_pending_order(
    client: AsyncClient,
    db_sql: AsyncSession,
    product_with_variant_in_stock: VarianteProducto,
    mocker
):
    """
    Test del nuevo flujo: create_preference crea una orden PENDIENTE
    sin descontar stock, y retorna la preferencia de MP.
    """
    # --- ARRANGE ---
    initial_stock = product_with_variant_in_stock.cantidad_en_stock
    quantity_to_buy = 2
    
    # Extraer precio ANTES de crear mocks (evita lazy loading issues)
    product_price = float(product_with_variant_in_stock.producto.precio)
    product_name = product_with_variant_in_stock.producto.nombre
    
    # Estructura correcta según el schema PreferenceRequest
    checkout_data = {
        "cart": {
            "user_id": "test-user-123",
            "items": [{
                "variante_id": product_with_variant_in_stock.id,
                "quantity": quantity_to_buy,
                "price": product_price,
                "name": product_name,
                "size": "M"
            }]
        },
        "shipping_address": {
            "firstName": "Test",
            "lastName": "User",
            "email": "test@example.com",
            "streetAddress": "Calle Test 123",
            "city": "Test City",
            "state": "Test State",
            "postalCode": "12345",
            "country": "Test Country",
            "phone": "1234567890"
        },
        "shipping_cost": 500.0
    }
    
    # Mock de la respuesta de MP SDK
    mock_preference_response = {
        "response": {
            "id": "test-preference-id-123",
            "init_point": "https://www.mercadopago.com/checkout/v1/redirect?pref_id=test"
        },
        "status": 201
    }
    
    mock_preference_obj = mocker.Mock()
    mock_preference_obj.create.return_value = mock_preference_response
    mocker.patch("routers.checkout_router.sdk.preference", return_value=mock_preference_obj)
    
    # Mock de Redis cache
    mocker.patch("routers.checkout_router.set_cache_async", return_value=None)
    
    # --- ACT ---
    response = await client.post("/api/checkout/create-preference", json=checkout_data)
    
    # --- ASSERT ---
    assert response.status_code == 200
    response_data = response.json()
    assert "init_point" in response_data
    assert "order_id" in response_data
    
    # Verificar que se creó la orden PENDIENTE
    order_id = response_data["order_id"]
    created_order = await db_sql.get(Orden, order_id)
    assert created_order is not None
    assert created_order.estado == "Pendiente"
    assert created_order.estado_pago == "Pendiente"
    assert created_order.usuario_id == "test-user-123"
    
    # Verificar que el stock NO se descontó
    await db_sql.refresh(product_with_variant_in_stock)
    assert product_with_variant_in_stock.cantidad_en_stock == initial_stock


@pytest.mark.asyncio
async def test_webhook_updates_pending_order_and_deducts_stock(
    client: AsyncClient,
    db_sql: AsyncSession,
    product_with_variant_in_stock: VarianteProducto,
    mocker
):
    """
    Test del webhook: cuando el pago es aprobado, actualiza la orden pendiente
    de 'Pendiente' a 'Completado' y descuenta el stock.
    """
    # --- ARRANGE ---
    # 1. Crear orden pendiente (simula el resultado de create_preference)
    initial_stock = product_with_variant_in_stock.cantidad_en_stock
    quantity_bought = 3
    
    # Extraer precio ANTES de acceder en contextos sincrónicos
    product_price = float(product_with_variant_in_stock.producto.precio)
    variant_id = product_with_variant_in_stock.id
    
    pending_order = Orden(
        usuario_id="test-user-123",
        monto_total=product_price * quantity_bought,
        estado="Pendiente",
        estado_pago="Pendiente",
        metodo_pago="Mercado Pago",
        payment_id_mercadopago=None,  # Aún no tiene payment_id
        direccion_envio={"streetAddress": "Calle Test 123"}
    )
    db_sql.add(pending_order)
    await db_sql.flush()
    order_id = pending_order.id
    
    # Agregar detalle de orden (sin descontar stock)
    from database.models import DetalleOrden
    detalle = DetalleOrden(
        orden_id=order_id,
        variante_producto_id=variant_id,
        cantidad=quantity_bought,
        precio_en_momento_compra=product_price
    )
    db_sql.add(detalle)
    await db_sql.commit()
    
    # 2. Preparar mock del pago aprobado en MP
    payment_id = "999888777"
    mock_payment_info_response = {
        "response": {
            "status": "approved",
            "external_reference": str(order_id),  # MP retorna el order_id que enviamos
            "transaction_amount": product_price * quantity_bought,
            "additional_info": {
                "items": [{
                    "id": str(variant_id),
                    "quantity": quantity_bought,
                    "unit_price": product_price
                }]
            },
            "payer": {"email": "test@example.com"}
        },
        "status": 200
    }
    
    mock_payment_object = mocker.Mock()
    mock_payment_object.get.return_value = mock_payment_info_response
    mocker.patch("routers.checkout_router.sdk.payment", return_value=mock_payment_object)
    
    # Mock del Celery task
    mocker.patch("routers.checkout_router.enviar_email_confirmacion_compra_task.delay")
    
    # Mock de Redis cache
    mocker.patch("routers.checkout_router.set_cache_async", return_value=None)
    
    # --- ACT ---
    # Enviar webhook con query params (como lo hace MP)
    response = await client.post(f"/api/checkout/webhook?id={payment_id}&topic=payment")
    
    # --- ASSERT ---
    assert response.status_code == 200
    
    # Recargar la orden desde DB
    await db_sql.refresh(pending_order)
    
    # Verificar que la orden se actualizó
    assert pending_order.estado == "Completado"
    assert pending_order.estado_pago == "Aprobado"
    assert pending_order.payment_id_mercadopago == payment_id
    
    # Verificar que el stock SÍ se descontó
    await db_sql.refresh(product_with_variant_in_stock)
    assert product_with_variant_in_stock.cantidad_en_stock == initial_stock - quantity_bought


@pytest.mark.asyncio
async def test_webhook_fails_if_insufficient_stock_on_approval(
    client: AsyncClient,
    db_sql: AsyncSession,
    product_with_variant_in_stock: VarianteProducto,
    mocker
):
    """
    Test: si cuando se aprueba el pago no hay stock suficiente,
    el webhook debe fallar y hacer rollback.
    """
    # --- ARRANGE ---
    initial_stock = product_with_variant_in_stock.cantidad_en_stock
    quantity_to_buy = initial_stock + 10  # Más de lo disponible
    
    # Extraer precio y variant_id ANTES de usar en mocks
    product_price = float(product_with_variant_in_stock.producto.precio)
    variant_id = product_with_variant_in_stock.id
    
    # 1. Crear orden pendiente
    pending_order = Orden(
        usuario_id="test-user-456",
        monto_total=product_price * quantity_to_buy,
        estado="Pendiente",
        estado_pago="Pendiente",
        metodo_pago="Mercado Pago",
        payment_id_mercadopago=None
    )
    db_sql.add(pending_order)
    await db_sql.flush()
    order_id = pending_order.id
    
    # Agregar detalle de orden
    from database.models import DetalleOrden
    detalle = DetalleOrden(
        orden_id=order_id,
        variante_producto_id=variant_id,
        cantidad=quantity_to_buy,
        precio_en_momento_compra=product_price
    )
    db_sql.add(detalle)
    await db_sql.commit()
    
    # 2. Mock del pago aprobado
    payment_id = "111222333"
    mock_payment_info_response = {
        "response": {
            "status": "approved",
            "external_reference": str(order_id),
            "transaction_amount": product_price * quantity_to_buy,
            "payer": {"email": "test@example.com"}
        },
        "status": 200
    }
    
    mock_payment_object = mocker.Mock()
    mock_payment_object.get.return_value = mock_payment_info_response
    mocker.patch("routers.checkout_router.sdk.payment", return_value=mock_payment_object)
    
    # --- ACT ---
    response = await client.post(f"/api/checkout/webhook?id={payment_id}&topic=payment")
    
    # --- ASSERT ---
    assert response.status_code == 500  # Error por stock insuficiente
    
    # Recargar orden - debe seguir en Pendiente (rollback)
    await db_sql.refresh(pending_order)
    assert pending_order.estado == "Pendiente"
    assert pending_order.payment_id_mercadopago is None
    
    # Verificar que el stock NO cambió
    await db_sql.refresh(product_with_variant_in_stock)
    assert product_with_variant_in_stock.cantidad_en_stock == initial_stock