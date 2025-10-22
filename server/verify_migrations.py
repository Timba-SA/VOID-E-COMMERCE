"""
Script para verificar que las migraciones se aplicaron correctamente.
"""

import asyncio
from sqlalchemy import text, select
from database.database import setup_database_engine
from database.models import Categoria

async def verify_migrations():
    """Verifica que las migraciones se aplicaron correctamente."""
    
    setup_database_engine()
    from database.database import engine as db_engine, AsyncSessionLocal
    
    print("=" * 60)
    print("VERIFICACIÓN DE MIGRACIONES")
    print("=" * 60)
    
    # Verificar categorías con traducciones
    print("\n📋 VERIFICANDO CATEGORÍAS CON TRADUCCIONES:\n")
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Categoria))
        categories = result.scalars().all()
        
        for cat in categories:
            i18n_info = cat.nombre_i18n if cat.nombre_i18n else "❌ Sin traducciones"
            print(f"  • ID: {cat.id} | Nombre: {cat.nombre}")
            print(f"    └─ Traducciones: {i18n_info}")
    
    # Verificar índices
    print("\n🔍 VERIFICANDO ÍNDICES CREADOS:\n")
    
    async with db_engine.connect() as conn:
        check_indexes_sql = """
            SELECT 
                tablename, 
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND indexname LIKE 'idx_%'
            ORDER BY tablename, indexname;
        """
        result = await conn.execute(text(check_indexes_sql))
        indexes = result.fetchall()
        
        current_table = None
        for idx in indexes:
            if current_table != idx[0]:
                current_table = idx[0]
                print(f"\n  📁 Tabla: {current_table}")
            print(f"    ✅ {idx[1]}")
        
        print(f"\n  Total de índices: {len(indexes)}")
    
    print("\n" + "=" * 60)
    print("✨ VERIFICACIÓN COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(verify_migrations())
