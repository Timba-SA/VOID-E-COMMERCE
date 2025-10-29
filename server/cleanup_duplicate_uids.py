"""
Script para limpiar UIDs duplicados antes de aplicar UNIQUE constraint
"""

import asyncio
from sqlalchemy import text
from database import database

async def cleanup_duplicate_uids():
    """Limpia UIDs duplicados manteniendo solo el más reciente"""
    
    print("🔧 Iniciando limpieza de UIDs duplicados...")
    
    # Inicializar el engine de la base de datos
    if database.AsyncSessionLocal is None:
        print("📦 Inicializando engine de base de datos...")
        database.setup_database_engine()
    
    async with database.AsyncSessionLocal() as session:
        try:
            # 1. Encontrar UIDs duplicados
            print("🔍 Buscando UIDs duplicados...")
            result = await session.execute(text("""
                SELECT uid, COUNT(*) as count
                FROM email_tasks
                WHERE uid IS NOT NULL
                GROUP BY uid
                HAVING COUNT(*) > 1
                ORDER BY COUNT(*) DESC
            """))
            
            duplicates = result.fetchall()
            
            if not duplicates:
                print("✅ No hay UIDs duplicados")
                return
            
            print(f"⚠️ Encontrados {len(duplicates)} UIDs duplicados:")
            for dup in duplicates[:5]:  # Mostrar solo los primeros 5
                print(f"   - UID '{dup[0]}': {dup[1]} registros")
            
            # 2. Para cada UID duplicado, mantener solo el más reciente
            print("\n🧹 Eliminando registros duplicados (manteniendo el más reciente)...")
            
            for uid_value, count in duplicates:
                # Eliminar todos excepto el más reciente
                await session.execute(text("""
                    DELETE FROM email_tasks
                    WHERE uid = :uid
                    AND id NOT IN (
                        SELECT id 
                        FROM email_tasks 
                        WHERE uid = :uid
                        ORDER BY creado_en DESC 
                        LIMIT 1
                    )
                """), {"uid": uid_value})
            
            await session.commit()
            print(f"✅ {len(duplicates)} grupos de UIDs duplicados limpiados")
            
            # 3. Verificar que no queden duplicados
            print("\n🔍 Verificando limpieza...")
            result = await session.execute(text("""
                SELECT COUNT(DISTINCT uid) as unique_uids,
                       COUNT(*) as total_records
                FROM email_tasks
                WHERE uid IS NOT NULL
            """))
            
            stats = result.fetchone()
            print(f"📊 UIDs únicos: {stats[0]}")
            print(f"📊 Total de registros: {stats[1]}")
            
            if stats[0] == stats[1]:
                print("✅ ¡Todos los UIDs son únicos ahora!")
            else:
                print(f"⚠️ Aún hay {stats[1] - stats[0]} registros con UIDs duplicados")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ ERROR durante la limpieza: {e}")
            raise

if __name__ == "__main__":
    print("=" * 60)
    print("  LIMPIEZA DE UIDs DUPLICADOS EN EMAIL_TASKS")
    print("=" * 60)
    print()
    
    asyncio.run(cleanup_duplicate_uids())
    
    print()
    print("=" * 60)
    print("✅ Limpieza finalizada. Ahora podés aplicar la migración.")
    print("=" * 60)
