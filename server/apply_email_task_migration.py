"""
Script para aplicar manualmente la migración de EmailTask
Agrega los campos necesarios para las optimizaciones del worker IA
"""

import asyncio
from sqlalchemy import text
from database import database

async def apply_migration():
    """Aplica los cambios de DB para EmailTask optimizado"""
    
    print("🔧 Iniciando migración de EmailTask...")
    
    # Inicializar el engine de la base de datos
    if database.AsyncSessionLocal is None:
        print("📦 Inicializando engine de base de datos...")
        database.setup_database_engine()
    
    async with database.AsyncSessionLocal() as session:
        try:
            # 1. Agregar columna error_message
            print("📝 Agregando columna 'error_message'...")
            try:
                await session.execute(text(
                    "ALTER TABLE email_tasks ADD COLUMN IF NOT EXISTS error_message TEXT"
                ))
                print("✅ Columna 'error_message' agregada")
            except Exception as e:
                print(f"⚠️ error_message: {e}")
            
            # 2. Agregar columna last_attempt_at
            print("📝 Agregando columna 'last_attempt_at'...")
            try:
                await session.execute(text(
                    "ALTER TABLE email_tasks ADD COLUMN IF NOT EXISTS last_attempt_at TIMESTAMP"
                ))
                print("✅ Columna 'last_attempt_at' agregada")
            except Exception as e:
                print(f"⚠️ last_attempt_at: {e}")
            
            # 3. Hacer uid NOT NULL (primero actualizar valores nulos)
            print("📝 Actualizando UIDs nulos...")
            try:
                result = await session.execute(text(
                    "UPDATE email_tasks SET uid = CAST(id AS VARCHAR) WHERE uid IS NULL"
                ))
                rows_updated = result.rowcount
                print(f"✅ {rows_updated} registros actualizados con UID")
            except Exception as e:
                print(f"⚠️ actualizar UIDs: {e}")
            
            print("📝 Haciendo UID NOT NULL...")
            try:
                await session.execute(text(
                    "ALTER TABLE email_tasks ALTER COLUMN uid SET NOT NULL"
                ))
                print("✅ UID es NOT NULL")
            except Exception as e:
                print(f"⚠️ uid NOT NULL: {e}")
            
            # 4. Agregar constraint UNIQUE a uid
            print("📝 Agregando UNIQUE constraint a UID...")
            try:
                await session.execute(text(
                    "ALTER TABLE email_tasks ADD CONSTRAINT uq_email_tasks_uid UNIQUE (uid)"
                ))
                print("✅ UNIQUE constraint agregado a UID")
            except Exception as e:
                print(f"⚠️ UNIQUE constraint: {e}")
            
            # 5. Agregar índice en status
            print("📝 Agregando índice en 'status'...")
            try:
                await session.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_email_tasks_status ON email_tasks(status)"
                ))
                print("✅ Índice en 'status' creado")
            except Exception as e:
                print(f"⚠️ índice status: {e}")
            
            # Commit de todos los cambios
            await session.commit()
            print("\n🎉 ¡Migración completada exitosamente!")
            
            # Mostrar estructura actual de la tabla
            print("\n📊 Verificando estructura de email_tasks...")
            result = await session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'email_tasks'
                ORDER BY ordinal_position
            """))
            
            print("\n📋 Columnas de email_tasks:")
            for row in result:
                nullable = "NULL" if row[2] == "YES" else "NOT NULL"
                print(f"  - {row[0]}: {row[1]} ({nullable})")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ ERROR durante la migración: {e}")
            raise

if __name__ == "__main__":
    print("=" * 60)
    print("  MIGRACIÓN DE OPTIMIZACIONES PARA EMAIL_TASKS")
    print("=" * 60)
    print()
    
    asyncio.run(apply_migration())
    
    print()
    print("=" * 60)
    print("✅ Migración finalizada. El worker optimizado ya puede usarse.")
    print("=" * 60)
