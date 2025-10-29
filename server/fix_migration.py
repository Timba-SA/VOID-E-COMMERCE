"""Script para aplicar migración correctamente"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from settings import settings

async def apply_migration():
    # Usar la URL de la base de datos desde las variables de entorno
    DB_URL = settings.DB_SQL_URI
    if not DB_URL:
        raise ValueError("❌ DB_SQL_URI no está configurada en las variables de entorno")
    
    engine = create_async_engine(DB_URL)
    
    async with engine.begin() as conn:
        print("\n🔧 Aplicando migración de EmailTask...\n")
        
        # 1. Agregar error_message
        try:
            await conn.execute(text("""
                ALTER TABLE email_tasks 
                ADD COLUMN IF NOT EXISTS error_message TEXT
            """))
            print("✅ Columna error_message agregada")
        except Exception as e:
            print(f"⚠️ Error agregando error_message: {e}")
        
        # 2. Agregar last_attempt_at
        try:
            await conn.execute(text("""
                ALTER TABLE email_tasks 
                ADD COLUMN IF NOT EXISTS last_attempt_at TIMESTAMP
            """))
            print("✅ Columna last_attempt_at agregada")
        except Exception as e:
            print(f"⚠️ Error agregando last_attempt_at: {e}")
        
        # 3. Crear índice en status
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_email_tasks_status 
                ON email_tasks(status)
            """))
            print("✅ Índice en status creado")
        except Exception as e:
            print(f"⚠️ Error creando índice: {e}")
    
    # Verificar columnas finales
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='email_tasks' 
            ORDER BY ordinal_position
        """))
        
        print("\n📋 Columnas finales de email_tasks:\n")
        for row in result:
            print(f"  - {row[0]}: {row[1]}")
    
    await engine.dispose()
    print("\n🎉 Migración completada!\n")

asyncio.run(apply_migration())
