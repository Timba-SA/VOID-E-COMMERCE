# En BACKEND/database/database.py

from settings import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from motor.motor_asyncio import AsyncIOMotorClient


# --- 1. CONFIGURACIÓN DE LA BASE DE DATOS SQL (MySQL) ---
DATABASE_URL = settings.DB_SQL_URI

# El engine es necesario para el lifespan en main.py y para el chequeo
engine = create_async_engine(DATABASE_URL)

# Creamos un sessionmaker asíncrono
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependencia para obtener una sesión de base de datos asíncrona
async def get_db() -> AsyncSession: # type: ignore
    async with AsyncSessionLocal() as session:
        yield session

async def check_sql_connection():
    """Verifica la conexión con la base de datos MySQL."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return {"database": "MySQL", "status": "ok", "message": "Conexión exitosa."}
    except Exception as e:
        return {"database": "MySQL", "status": "error", "message": str(e)}

# --- 2. CONFIGURACIÓN DE LA BASE DE DATOS NoSQL (MongoDB) ---
MONGO_URI = settings.DB_NOSQL_URI

# CORREGIDO: Creamos el cliente y obtenemos la base de datos por defecto desde la URI
client = AsyncIOMotorClient(MONGO_URI)
db_nosql = client.get_database()

# Dependencia para la base de datos NoSQL que usarán tus routers
async def get_db_nosql():
    yield db_nosql

async def check_nosql_connection():
    """Verifica la conexión con la base de datos MongoDB."""
    try:
        await client.admin.command('ping')
        return {"database": "MongoDB", "status": "ok", "message": "Conexión exitosa."}
    except Exception as e:
        return {"database": "MongoDB", "status": "error", "message": str(e)}