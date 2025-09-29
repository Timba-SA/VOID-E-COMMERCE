import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
async def test_add_item_to_cart(authenticated_client: AsyncClient, test_variant: dict):
    """Prueba agregar un item al carrito de un usuario autenticado."""
    response = await authenticated_client.post(
        "/api/cart/items",
        json=test_variant
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["variante_id"] == test_variant["variante_id"]
    assert data["items"][0]["quantity"] == test_variant["quantity"]

@pytest.mark.asyncio
async def test_view_cart(authenticated_client: AsyncClient, test_variant: dict):
    """Prueba ver el contenido del carrito."""
    # Primero agregamos un item
    await authenticated_client.post(
        "/api/cart/items",
        json=test_variant
    )

    response = await authenticated_client.get("/api/cart/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["variante_id"] == test_variant["variante_id"]

@pytest.mark.asyncio
async def test_remove_item_from_cart(authenticated_client: AsyncClient, test_variant: dict):
    """Prueba eliminar un item del carrito."""
    # Agregamos un item primero
    await authenticated_client.post(
        "/api/cart/items",
        json=test_variant
    )
    
    # Luego lo eliminamos
    response = await authenticated_client.delete(f"/api/cart/items/{test_variant['variante_id']}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 0
