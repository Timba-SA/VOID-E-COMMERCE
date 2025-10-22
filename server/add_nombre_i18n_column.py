"""
Script para agregar la columna nombre_i18n a la tabla categorias.
Ejecutar ANTES de migrate_categories_i18n.py
"""

import asyncio
from sqlalchemy import text
from database.database import setup_database_engine, engine

async def add_column():
    """Agrega la columna nombre_i18n a la tabla categorias."""
    
    setup_database_engine()
    
    # Importar el engine después de configurarlo
    from database.database import engine as db_engine
    
    async with db_engine.connect() as conn:
        try:
            print("🔧 Verificando si la columna nombre_i18n existe...")
            
            # Verificar si la columna ya existe
            check_sql = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='categorias' 
                AND column_name='nombre_i18n';
            """
            result = await conn.execute(text(check_sql))
            exists = result.fetchone()
            
            if exists:
                print("✅ La columna nombre_i18n ya existe. No es necesario agregarla.")
                return
            
            print("📝 Agregando columna nombre_i18n a la tabla categorias...")
            
            # Agregar la columna
            alter_sql = """
                ALTER TABLE categorias 
                ADD COLUMN IF NOT EXISTS nombre_i18n JSON;
            """
            await conn.execute(text(alter_sql))
            await conn.commit()
            
            print("✅ Columna nombre_i18n agregada exitosamente!")
            print("\n🎉 Ahora puedes ejecutar migrate_categories_i18n.py")
            
        except Exception as e:
            print(f"❌ Error al agregar columna: {e}")
            await conn.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(add_column())
