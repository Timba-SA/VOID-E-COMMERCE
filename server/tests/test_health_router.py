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
async def test_health_check_nosql_ok(client: AsyncClient, mocker): # <-- Mocker sigue siendo necesario
    """Prueba el endpoint /health/db-nosql."""

    # =======================================================================
    # ¡AQUÍ ESTÁ EL ARREGLO FINAL!
    # =======================================================================
    # Engañamos a la ruta: cuando el endpoint intente llamar a 'check_nosql_connection',
    # en realidad va a llamar a nuestro doble, que devuelve "ok" al instante.
    # La ruta del engaño es 'donde_se_usa.lo_que_quiero_reemplazar'.
    mocker.patch(
        "routers.health_router.check_nosql_connection",
        return_value={"database": "MongoDB", "status": "ok", "message": "Conexión mockeada exitosamente!"}
    )
    # =======================================================================

    # El resto del test ahora va a funcionar porque la llamada de arriba nunca falla.
    response = await client.get("/health/db-nosql")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
