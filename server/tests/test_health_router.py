import pytest
from httpx import AsyncClient

# No necesitamos sobreescribir las dependencias aquí porque
# el fixture `client` en conftest.py ya lo hace.

@pytest.mark.asyncio
async def test_health_check_sql_ok(client: AsyncClient):
    """Prueba el endpoint /health/db-sql."""
    response = await client.get("/health/db-sql")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_health_check_nosql_ok(client: AsyncClient):
    """Prueba el endpoint /health/db-nosql."""
    response = await client.get("/health/db-nosql")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
