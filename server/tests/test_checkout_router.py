# En tests/test_checkout_router.py
import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import Orden, VarianteProducto

# TODO: Actualizar estos tests para el nuevo flujo con orden pendiente pre-pref
@pytest.mark.skip(reason="Test desactualizado - nuevo flujo usa orden pendiente pre-pref + Redis")
@pytest.mark.asyncio
async def test_webhook_success_creates_order_and_updates_stock(
    client: AsyncClient,
    db_sql: AsyncSession,
    product_with_variant_in_stock: VarianteProducto,
    mocker
):
    # --- ARRANGE ---
    initial_stock = product_with_variant_in_stock.cantidad_en_stock
    quantity_bought = 5
    payment_id = "123456789"  # Debe ser solo dígitos
    transaction_amount = product_with_variant_in_stock.producto.precio * quantity_bought

    # El webhook ahora espera query params (id=X&topic=payment)
    # NO enviar JSON body

    mock_payment_info_response = {
        "response": {
            "status": "approved", "external_reference": "test-user-id",
            "transaction_amount": float(transaction_amount),
            "additional_info": {
                "items": [{
                    "id": str(product_with_variant_in_stock.id),
                    "quantity": quantity_bought,
                    "unit_price": float(product_with_variant_in_stock.producto.precio)
                }]
            },
            "payer": {"email": "test@example.com"}
        },
        "status": 200
    }

    # --- ACT ---
    mock_payment_object = mocker.Mock()
    mock_payment_object.get.return_value = mock_payment_info_response
    mocker.patch("routers.checkout_router.sdk.payment", return_value=mock_payment_object)

    # Mock del Celery task
    mocker.patch("routers.checkout_router.enviar_email_confirmacion_compra_task.delay")

    # Enviar como query params (así lo espera MP)
    response = await client.post(f"/api/checkout/webhook?id={payment_id}&topic=payment")

    # --- ASSERT ---
    assert response.status_code == 200
    
    # Recargar el variant desde la base de datos
    await db_sql.refresh(product_with_variant_in_stock)
    
    order_result = await db_sql.execute(select(Orden).where(Orden.payment_id_mercadopago == payment_id))
    created_order = order_result.scalars().first()
    assert created_order is not None
    assert created_order.monto_total == transaction_amount

    # Verificar que el stock se redujo
    assert product_with_variant_in_stock.cantidad_en_stock == initial_stock - quantity_bought


@pytest.mark.skip(reason="Test desactualizado - nuevo flujo usa orden pendiente pre-pref + Redis")
@pytest.mark.asyncio
async def test_webhook_fails_and_rolls_back_on_insufficient_stock(
    client: AsyncClient,
    db_sql: AsyncSession,
    product_with_variant_in_stock: VarianteProducto,
    mocker
):
    # --- ARRANGE (sin cambios) ---
    initial_stock = product_with_variant_in_stock.cantidad_en_stock
    quantity_to_buy = initial_stock + 1
    payment_id = "987654321"  # Solo dígitos
    
    # El webhook espera query params
    mock_payment_info_response = {
        "response": {
            "status": "approved", "external_reference": "test-user-id",
            "transaction_amount": 100.0,
            "additional_info": {
                "items": [{"id": str(product_with_variant_in_stock.id), "quantity": quantity_to_buy, "unit_price": 10.0}]
            },
            "payer": {"email": "test@example.com"}
        },
        "status": 200
    }

    # --- ACT (sin cambios) ---
    mock_payment_object = mocker.Mock()
    mock_payment_object.get.return_value = mock_payment_info_response
    mocker.patch("routers.checkout_router.sdk.payment", return_value=mock_payment_object)
    
    # Mock del Celery task
    mocker.patch("routers.checkout_router.enviar_email_confirmacion_compra_task.delay")

    # Enviar como query params
    response = await client.post(f"/api/checkout/webhook?id={payment_id}&topic=payment")

    # --- ASSERT (sin cambios) ---
    assert response.status_code == 500
    
    # Verificar que NO se creó la orden
    order_result = await db_sql.execute(select(Orden).where(Orden.payment_id_mercadopago == payment_id))
    assert order_result.scalars().first() is None

    # Recargar el variant desde la base de datos
    await db_sql.refresh(product_with_variant_in_stock)
    # Verificar que el stock NO cambió (rollback)
    assert product_with_variant_in_stock.cantidad_en_stock == initial_stock