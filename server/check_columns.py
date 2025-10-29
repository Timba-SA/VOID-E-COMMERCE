"""Script para verificar columnas de email_tasks"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from settings import settings

async def check_columns():
    # Usar la URL de la base de datos desde las variables de entorno
    DB_URL = settings.DB_SQL_URI
    if not DB_URL:
        raise ValueError("❌ DB_SQL_URI no está configurada en las variables de entorno")
    
    engine = create_async_engine(DB_URL)
    
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name='email_tasks' 
            ORDER BY ordinal_position
        """))
        
        print("\n📋 Columnas actuales de email_tasks:\n")
        for row in result:
            nullable = "NULL" if row[2] == 'YES' else "NOT NULL"
            print(f"  - {row[0]}: {row[1]} ({nullable})")
    
    await engine.dispose()

asyncio.run(check_columns())
