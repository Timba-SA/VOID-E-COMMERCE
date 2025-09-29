# Contenido para routers/health_router.py (versión con 2 chequeos)

from fastapi import APIRouter
from database.database import check_sql_connection, check_nosql_connection

router = APIRouter(
    prefix="/health",
    tags=["Health Checks"]
)

@router.get("/db-sql")
async def check_sql_database():
    """Verifica que la conexión con MySQL funcione."""
    return await check_sql_connection()

@router.get("/db-nosql")
async def check_nosql_database():
    """Verifica que la conexión con MongoDB funcione."""
    return await check_nosql_connection()