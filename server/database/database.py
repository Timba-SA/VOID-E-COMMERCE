# /server/database/database.py

import os
from settings import settings # Para leer las URLs
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession # AsyncSession está aquí
# from sqlalchemy.orm import sessionmaker # sessionmaker es para síncrono, usamos async_sessionmaker
from sqlalchemy.ext.asyncio import async_sessionmaker # <--- ESTA ES LA CORRECTA PARA ASYNC
from sqlalchemy import text
from sqlalchemy.pool import NullPool
from motor.motor_asyncio import AsyncIOMotorClient
import logging

logger = logging.getLogger(__name__)

# --- 1. CONFIGURACIÓN DE LA BASE DE DATOS SQL (PostgreSQL/Supabase) ---

# Variables globales inicializadas como None
engine = None
AsyncSessionLocal = None # Cambiamos el nombre para claridad

def setup_database_engine():
    """
    Crea e inicializa el engine y la fábrica de sesiones SQL asíncrona.
    Debe llamarse al inicio de la aplicación (lifespan).
    """
    global engine, AsyncSessionLocal # Indicar que modificaremos las globales

    # Solo configurar si no está ya hecho (importante para múltiples workers/tests)
    if engine is None:
        # 1. Leer la URL desde settings
        db_url_from_settings = settings.DB_SQL_URI # Usamos una variable local clara
        if not db_url_from_settings:
            logger.critical("🔥 DB_SQL_URI no está configurada en las variables de entorno.")
            raise ValueError("DB_SQL_URI no configurada. La aplicación no puede iniciar.")

        logger.info(f"Configurando motor de DB SQL para el proceso PID: {os.getpid()}")

        # 2. Imprimir la URL (CORREGIDO - usando la variable local)
        print(f"DEBUG: Configurando engine SQL con URL: {db_url_from_settings}") # <-- CORREGIDO

        try:
            # 3. Crear el engine Async con NullPool
            engine = create_async_engine(
                db_url_from_settings, # <-- Usa la variable local
                poolclass=NullPool
            )

            # 4. Crear el SessionLocal ASÍNCRONO usando async_sessionmaker
            AsyncSessionLocal = async_sessionmaker(
                bind=engine, # Bindear al engine recién creado
                class_=AsyncSession,
                expire_on_commit=False # Configuración común para FastAPI
            )
            logger.info("✅ Motor de base de datos SQL y AsyncSessionLocal configurados exitosamente.")

        except Exception as e:
            logger.critical(f"🔥 Error CRÍTICO al crear el engine SQL o AsyncSessionLocal: {e}", exc_info=True)
            # Si falla aquí, engine o AsyncSessionLocal pueden quedar como None
            # Lanzar un error detiene el inicio de la app, lo cual es bueno si la DB es esencial
            raise RuntimeError(f"Fallo al configurar la base de datos SQL: {e}") from e
    else:
        logger.info(f"El motor de la DB SQL ya estaba configurado para el proceso PID: {os.getpid()}.")


# Dependencia para obtener una sesión de base de datos asíncrona
async def get_db() -> AsyncSession:
    """Dependencia de FastAPI para obtener una sesión de DB SQL asíncrona."""
    if AsyncSessionLocal is None:
        logger.critical("CRITICAL: AsyncSessionLocal no está inicializado. La configuración inicial falló o no se ejecutó.")
        raise RuntimeError("La configuración de la sesión de la base de datos SQL (AsyncSessionLocal) no está disponible.")

    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback() # Hacer rollback en caso de error durante la request
            raise
        finally:
            await session.close() # Cerrar la sesión al finalizar

async def check_sql_connection():
    """Verifica la conexión con la base de datos SQL."""
    if engine is None:
        return {"database": "SQL", "status": "error", "message": "El motor de la DB no está inicializado."}
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            await connection.commit() # Algunas DBs necesitan commit incluso para SELECT 1
        return {"database": "SQL", "status": "ok", "message": f"Conexión exitosa (SELECT 1 -> {result.scalar_one()})."}
    except Exception as e:
        logger.error(f"Error al verificar conexión SQL: {e}", exc_info=True)
        return {"database": "SQL", "status": "error", "message": str(e)}

# --- 2. CONFIGURACIÓN DE LA BASE DE DATOS NoSQL (MongoDB) ---
# Se configura directamente al importar, ya que Motor lo maneja diferente
mongo_client = None
db_nosql = None

try:
    MONGO_URI = settings.DB_NOSQL_URI
    if not MONGO_URI:
        logger.warning("DB_NOSQL_URI no configurada.")
        # Decide si esto debe ser un error crítico o no
    else:
        # Es buena idea poner un timeout por si Mongo no responde rápido al inicio
        mongo_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Obtener el nombre de la base de datos de settings si está definido
        db_name = settings.DB_NOSQL_NAME if hasattr(settings, 'DB_NOSQL_NAME') else None
        if db_name:
             db_nosql = mongo_client[db_name] # Selecciona la DB por nombre
        else:
             # Si no hay nombre, Motor puede inferirlo de la URL o puedes poner uno por defecto
             db_nosql = mongo_client.get_database() # Motor intenta adivinar
             logger.warning(f"DB_NOSQL_NAME no definida, usando DB por defecto: {db_nosql.name}")
        # La conexión real se hace 'lazy' (cuando se usa), pero podemos forzar un ping
        # await mongo_client.admin.command('ping') # Mover el ping al lifespan si quieres verificar al inicio
        logger.info(f"✅ Cliente MongoDB configurado para URI (la conexión se probará en lifespan/uso). DB: {db_nosql.name if db_nosql else 'No Seleccionada'}")

except Exception as e:
    logger.error(f"🔥 Error al configurar el cliente MongoDB: {e}", exc_info=True)
    # Aquí mongo_client y db_nosql pueden quedar como None

# Dependencia para obtener la base de datos NoSQL
async def get_db_nosql():
    if db_nosql is None:
        logger.error("La base de datos NoSQL (MongoDB) no está inicializada correctamente.")
        raise RuntimeError("La conexión a MongoDB no está disponible.")
    yield db_nosql

async def check_nosql_connection():
    """Verifica la conexión con la base de datos MongoDB."""
    if mongo_client is None:
        return {"database": "MongoDB", "status": "error", "message": "Cliente MongoDB no inicializado."}
    try:
        await mongo_client.admin.command('ping')
        db_name_to_show = db_nosql.name if db_nosql else "N/A"
        return {"database": "MongoDB", "status": "ok", "message": f"Conexión exitosa (ping OK). DB: {db_name_to_show}"}
    except Exception as e:
        logger.error(f"Error al verificar conexión MongoDB: {e}", exc_info=True)
        return {"database": "MongoDB", "status": "error", "message": str(e)}

# Función para usar en scripts (si es necesario)
# async def get_db_async():
#     """Generador async para usar fuera de FastAPI (ej: scripts)."""
#     if AsyncSessionLocal is None:
#          setup_database_engine() # Asegurarse de que esté configurado
#     if AsyncSessionLocal is None: # Chequear de nuevo por si falló setup
#          raise RuntimeError("Fallo al configurar AsyncSessionLocal para get_db_async.")
#     async with AsyncSessionLocal() as session:
#          yield session