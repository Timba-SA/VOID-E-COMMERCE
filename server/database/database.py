# /database/database.py

import os
from settings import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from motor.motor_asyncio import AsyncIOMotorClient
import logging

logger = logging.getLogger(__name__)

# --- 1. CONFIGURACIÓN DE LA BASE DE DATOS SQL (MySQL) ---

# CAMBIO CLAVE: Inicializamos las variables en None.
# No creamos nada al importar el archivo.
engine = None
AsyncSessionLocal = None

def setup_database_engine():
    """
    Esta función crea e inicializa el engine y la fábrica de sesiones SQL.
    Será llamada por la señal de Celery en cada proceso worker.
    """
    global engine, AsyncSessionLocal  # Usamos 'global' para modificar las variables del módulo

    # Solo creamos el engine si no ha sido creado antes en este proceso
    if engine is None:
        DATABASE_URL = settings.DB_SQL_URI
        logger.info(f"Configurando motor de DB para el proceso worker PID: {os.getpid()}")
        
        engine = create_async_engine(DATABASE_URL)
        AsyncSessionLocal = sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        logger.info("✅ Motor de base de datos SQL configurado exitosamente.")
    else:
        logger.info("El motor de la DB ya estaba configurado para este proceso.")


# Dependencia para obtener una sesión de base de datos asíncrona
async def get_db() -> AsyncSession:
    if AsyncSessionLocal is None:
        logger.critical("AsyncSessionLocal no está inicializado. El worker de Celery no llamó a setup_database_engine.")
        raise RuntimeError("La sesión de la base de datos no está disponible.")
    
    async with AsyncSessionLocal() as session:
        yield session

async def check_sql_connection():
    """Verifica la conexión con la base de datos MySQL."""
    if engine is None:
        return {"database": "MySQL", "status": "error", "message": "El motor de la DB no está inicializado."}
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return {"database": "MySQL", "status": "ok", "message": "Conexión exitosa."}
    except Exception as e:
        return {"database": "MySQL", "status": "error", "message": str(e)}

# --- 2. CONFIGURACIÓN DE LA BASE DE DATOS NoSQL (MongoDB) ---
# Esta parte no necesita cambios para nuestro problema, está perfecta.
MONGO_URI = settings.DB_NOSQL_URI
client = AsyncIOMotorClient(MONGO_URI)
db_nosql = client.get_database()

async def get_db_nosql():
    yield db_nosql

async def check_nosql_connection():
    """Verifica la conexión con la base de datos MongoDB."""
    try:
        await client.admin.command('ping')
        return {"database": "MongoDB", "status": "ok", "message": "Conexión exitosa."}
    except Exception as e:
        return {"database": "MongoDB", "status": "error", "message": str(e)}