# /server/scripts/create_tables.py

import asyncio
import logging
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine

# Importamos las settings para saber la URL de la DB
from settings import settings

# =================================================================
# Importamos los nombres CORRECTOS de tu models.py
# =================================================================
from database.models import (
    Base,
    Categoria,
    Producto,
    VarianteProducto,
    Orden,
    DetalleOrden,
    Gasto,
    ConversacionIA,
    EmailTask,
    WishlistItem
)

# Configuramos un logger básico para ver qué pasa
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Esta es la URL de Supabase que tenés en tu .env
DATABASE_URL = settings.DB_SQL_URI

async def init_db():
    if not DATABASE_URL:
        logger.critical("¡ERROR! No se encontró la variable DB_SQL_URI en tu .env")
        return

    logger.info(f"Conectando a la base de datos: ...{DATABASE_URL.split('@')[-1]}")
    
    # Creamos el motor asíncrono
    engine = create_async_engine(DATABASE_URL)

    async with engine.begin() as conn:
        logger.info("Eliminando tablas viejas (si existen)...")
        await conn.run_sync(Base.metadata.drop_all)
        
        logger.info("Creando tablas nuevas...")
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    logger.info("✅ ¡Tablas creadas en Supabase, papá!")

if __name__ == "__main__":
    logger.info("Iniciando script de creación de tablas...")
    asyncio.run(init_db())