# /server/database/database.py

import os
from settings import settings # Para leer las URLs
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker # Importar async_sessionmaker
from sqlalchemy import text
from motor.motor_asyncio import AsyncIOMotorClient
import logging

logger = logging.getLogger(__name__)

# --- 1. CONFIGURACIÓN DE LA BASE DE DATOS SQL (PostgreSQL/Supabase) ---

# Variables globales inicializadas como None
engine = None
AsyncSessionLocal = None # Usamos este nombre consistentemente

def setup_database_engine():
    """
    Configura el motor de base de datos SQLAlchemy asíncrono y AsyncSessionLocal.
    Debe llamarse una vez al inicio (ej: lifespan).
    """
    global engine, AsyncSessionLocal

    if engine is None:
        db_url = settings.DB_SQL_URI # Guardar en variable local 'db_url'
        if not db_url:
            logger.critical("🔥 DB_SQL_URI no está configurada en las variables de entorno.")
            raise ValueError("DB_SQL_URI no configurada.")

        logger.info(f"Configurando motor de DB SQL para el proceso PID: {os.getpid()}")

        # 2. Imprimir la URL (¡¡¡CORREGIDO!!!)
        print("DEBUG: Configurando engine SQL con URL:")
        print(db_url) # Imprimir la URL en una línea separada

        try:
            # Configuración especial para Supabase Connection Pooler
            # Si usas el pooler (puerto 6543), necesitas desactivar prepared statements
            connect_args = {
                "server_settings": {
                    "application_name": f"void_worker_{os.getpid()}"
                }
            }
            
            # Detectar si estamos usando el Connection Pooler (puerto 6543 o 5432)
            if ":6543" in db_url:
                logger.info("🔌 Connection Pooler detectado (puerto 6543) - desactivando prepared statements")
                connect_args["prepared_statement_cache_size"] = 0
                connect_args["statement_cache_size"] = 0
            elif ":5432" in db_url and "pooler.supabase.com" in db_url:
                logger.info("🔌 Supabase Transaction Pooler detectado (puerto 5432) - optimizando conexiones")
                connect_args["prepared_statement_cache_size"] = 0
                connect_args["statement_cache_size"] = 0
            
            # Configuración optimizada del pool para Celery Workers
            # NullPool NO es bueno para workers, usar QueuePool con límites conservadores
            pool_config = {
                "pool_size": 5,              # Conexiones permanentes por worker
                "max_overflow": 10,          # Conexiones adicionales en picos
                "pool_timeout": 30,          # Timeout esperando conexión del pool
                "pool_recycle": 300,         # Reciclar conexiones cada 5 min (evita timeouts de Supabase)
                "pool_pre_ping": True,       # CRÍTICO: Verificar conexión antes de usar
                "echo_pool": False,          # Logs del pool (debug)
            }
            
            # Si es un worker de Celery, reducir pool_size
            if "celery" in os.environ.get("CELERY_WORKER_NAME", "").lower():
                pool_config["pool_size"] = 2
                pool_config["max_overflow"] = 3
                logger.info("🔧 Configuración de pool reducida para Celery worker")
            
            engine = create_async_engine(
                db_url,
                connect_args=connect_args,
                **pool_config
            )

            AsyncSessionLocal = async_sessionmaker(
                bind=engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            logger.info("✅ Motor de base de datos SQL y AsyncSessionLocal configurados exitosamente.")

        except Exception as e:
            logger.critical(f"🔥 Error CRÍTICO al crear el engine SQL o AsyncSessionLocal: {e}", exc_info=True)
            engine = None
            AsyncSessionLocal = None
            raise RuntimeError(f"Fallo al configurar la base de datos SQL: {e}") from e
    else:
        logger.info(f"El motor de la DB SQL ya estaba configurado para el proceso PID: {os.getpid()}.")


async def get_db() -> AsyncSession:
    """Dependencia de FastAPI para obtener una sesión de DB SQL asíncrona."""
    if AsyncSessionLocal is None:
        # Este log es importante si setup_database_engine falló
        logger.critical("CRITICAL: AsyncSessionLocal no está inicializado. La configuración inicial falló o no se ejecutó.")
        raise RuntimeError("La configuración de la sesión de la base de datos SQL (AsyncSessionLocal) no está disponible.")

    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def check_sql_connection():
    """Verifica la conexión con la base de datos SQL."""
    # Llama a setup_database_engine() por si acaso no se llamó en lifespan (aunque debería)
    # Es mejor asegurarse que se llame solo una vez al inicio.
    # setup_database_engine() # Comentado - Asumimos que lifespan lo llama.

    if engine is None:
        return {"database": "SQL", "status": "error", "message": "El motor de la DB SQL no está inicializado."}
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            scalar_result = result.scalar_one_or_none() # Usar scalar_one_or_none para seguridad
        # No necesitas commit para SELECT 1
        return {"database": "SQL", "status": "ok", "message": f"Conexión exitosa (SELECT 1 -> {scalar_result})."}
    except Exception as e:
        logger.error(f"Error al verificar conexión SQL: {e}", exc_info=False) # No mostrar Traceback completo aquí
        return {"database": "SQL", "status": "error", "message": f"Fallo al conectar o ejecutar SELECT 1: {e}"}

# --- 2. CONFIGURACIÓN DE LA BASE DE DATOS NoSQL (MongoDB) ---
mongo_client = None
db_nosql = None

try:
    MONGO_URI = settings.DB_NOSQL_URI
    if not MONGO_URI:
        logger.warning("DB_NOSQL_URI no configurada.")
    else:
        mongo_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Obtener el nombre de la base de datos de settings
        db_name = getattr(settings, 'DB_NOSQL_NAME', None) # Forma segura de obtener el atributo
        if db_name:
             db_nosql = mongo_client[db_name]
        else:
             db_nosql = mongo_client.get_database() # Motor intenta adivinar
             logger.warning(f"DB_NOSQL_NAME no definida en settings, usando DB por defecto: {db_nosql.name if db_nosql is not None else 'Desconocida'}")

        # --- CORRECCIÓN DEL LOG DE MONGO ---
        db_name_to_log = db_nosql.name if db_nosql is not None else 'No Seleccionada'
        logger.info(f"✅ Cliente MongoDB configurado para URI. DB: {db_name_to_log}")
        # Mover el ping a lifespan o a check_nosql_connection

except Exception as e:
    logger.error(f"🔥 Error al configurar el cliente MongoDB: {e}", exc_info=True)
    mongo_client = None # Asegurar que queden None si falla
    db_nosql = None

async def get_db_nosql():
    """Dependencia de FastAPI para obtener la instancia de la DB NoSQL."""
    if db_nosql is None:
        logger.error("La base de datos NoSQL (MongoDB) no está inicializada correctamente.")
        raise RuntimeError("La conexión a MongoDB no está disponible.")
    # No necesitas yield aquí si devuelves la instancia directamente
    return db_nosql # Devolver la instancia db_nosql

async def check_nosql_connection():
    """Verifica la conexión con la base de datos MongoDB."""
    if mongo_client is None:
        return {"database": "MongoDB", "status": "error", "message": "Cliente MongoDB no inicializado."}
    try:
        await mongo_client.admin.command('ping')
        db_name_to_show = db_nosql.name if db_nosql is not None else "N/A"
        return {"database": "MongoDB", "status": "ok", "message": f"Conexión exitosa (ping OK). DB: {db_name_to_show}"}
    except Exception as e:
        logger.error(f"Error al verificar conexión MongoDB: {e}", exc_info=False)
        return {"database": "MongoDB", "status": "error", "message": f"Fallo en ping a MongoDB: {e}"}

# async def get_db_async(): # Comentada si no la usas en scripts
#     # ... (código anterior) ...