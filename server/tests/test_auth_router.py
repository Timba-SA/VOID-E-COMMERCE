# En tests/test_auth_router.py
import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
async def test_register_new_user(client: AsyncClient):
    """Prueba el registro de un nuevo usuario."""

    # --- FIX ---
    # Cambiamos 'username' por 'name' y 'last_name'
    # para coincidir con user_schemas.UserCreate
    response = await client.post(
        "/api/auth/register",
        json={
            "name": "New",
            "last_name": "User",
            "email": "new@example.com",
            "password": "newpassword"
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "New" # <-- FIX
    assert data["email"] == "new@example.com"
    
    # --- FIX DEFINITIVO ---
    # La API devuelve '_id', así que el test debe esperar '_id'.
    assert "_id" in data

@pytest.mark.asyncio
async def test_register_existing_user(client: AsyncClient, test_user: dict):
    """Prueba que no se puede registrar un usuario que ya existe."""
    
    # --- FIX ---
    # Cambiamos 'username' por 'name' y 'last_name'
    response = await client.post(
        "/api/auth/register",
        json={
            "name": test_user["name"],
            "last_name": test_user["last_name"],
            "email": test_user["email"], # Use the same email to trigger the error
            "password": "password",
        },
    )
    # El router devuelve 400 si el email existe
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_login_for_access_token(client: AsyncClient, test_user: dict):
    """Prueba el login exitoso y la obtención de un token."""
    response = await client.post(
        "/api/auth/login", data={"username": test_user["email"], "password": "password"} # Login with email
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user: dict):
    """Prueba el login con contraseña incorrecta."""
    response = await client.post(
        "/api/auth/login",
        data={"username": test_user["email"], "password": "wrongpassword"}, # Login with email
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_current_user(authenticated_client: AsyncClient, test_user: dict):
    """Prueba obtener los datos del usuario actualmente autenticado."""
    response = await authenticated_client.get("/api/auth/me")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # --- FIX ---
    # El schema UserOut no tiene 'username', usamos 'name'
    assert data["name"] == test_user["name"]
    assert data["email"] == test_user["email"]