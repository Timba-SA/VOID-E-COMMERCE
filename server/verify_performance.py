"""
Script de verificación de rendimiento y optimizaciones.
Ejecutar para confirmar que todas las optimizaciones están activas.
"""

import asyncio
import time
from sqlalchemy import text
from database.database import setup_database_engine

async def verify_indexes():
    """Verifica que todos los índices estén creados."""
    setup_database_engine()
    from database.database import engine as db_engine
    
    expected_indexes = [
        'idx_productos_categoria_precio',
        'idx_productos_categoria_stock',
        'idx_ordenes_usuario_estado',
        'idx_ordenes_fecha_estado',
        'idx_variantes_disponibles',
        'idx_productos_descripcion_gin',
        'idx_conversaciones_recientes',
    ]
    
    print("🔍 Verificando índices compuestos...")
    
    async with db_engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY indexname;
        """))
        
        existing_indexes = [row[0] for row in result]
        
        found = 0
        missing = []
        
        for idx in expected_indexes:
            if idx in existing_indexes:
                print(f"  ✅ {idx}")
                found += 1
            else:
                print(f"  ❌ {idx} - FALTA")
                missing.append(idx)
        
        print(f"\n📊 Resultado: {found}/{len(expected_indexes)} índices encontrados")
        
        if missing:
            print(f"⚠️ Índices faltantes: {', '.join(missing)}")
        else:
            print("✨ Todos los índices están creados!")
    
    return len(missing) == 0

async def test_query_performance():
    """Prueba el rendimiento de queries críticas."""
    setup_database_engine()
    from database.database import engine as db_engine
    
    print("\n⚡ Probando rendimiento de queries...")
    
    queries = [
        ("Productos por categoría", """
            SELECT * FROM productos 
            WHERE categoria_id = 1 
            LIMIT 10;
        """),
        ("Productos con filtro de precio", """
            SELECT * FROM productos 
            WHERE categoria_id = 1 AND precio < 50000
            ORDER BY precio ASC
            LIMIT 10;
        """),
        ("Órdenes de usuario", """
            SELECT * FROM ordenes 
            WHERE usuario_id = '123'
            ORDER BY creado_en DESC
            LIMIT 10;
        """),
        ("Variantes disponibles", """
            SELECT * FROM variantes_productos 
            WHERE cantidad_en_stock > 0
            LIMIT 10;
        """),
    ]
    
    async with db_engine.connect() as conn:
        for name, query in queries:
            start = time.time()
            await conn.execute(text(query))
            elapsed = (time.time() - start) * 1000  # ms
            
            status = "⚡ EXCELENTE" if elapsed < 50 else "✅ BUENO" if elapsed < 100 else "⚠️ LENTO"
            print(f"  {status} {name}: {elapsed:.2f}ms")

async def check_cache_service():
    """Verifica que Redis esté funcionando."""
    print("\n💾 Verificando servicio de cache...")
    
    try:
        from services import cache_service
        
        # Test de escritura
        test_key = "test:performance"
        test_value = "Hello Redis!"
        
        cache_service.set_cache(test_key, test_value, ttl=10)
        retrieved = cache_service.get_cache(test_key)
        
        if retrieved == test_value:
            print("  ✅ Redis funcionando correctamente")
            print(f"  ✅ Escritura y lectura exitosas")
            
            # Limpiar
            cache_service.delete_cache(test_key)
            return True
        else:
            print("  ❌ Redis no está devolviendo valores correctos")
            return False
            
    except Exception as e:
        print(f"  ❌ Error al conectar con Redis: {e}")
        print(f"  💡 Asegúrate de que Redis esté corriendo en Docker")
        return False

async def check_gzip_middleware():
    """Verifica que GZIP esté configurado."""
    print("\n🗜️ Verificando compresión GZIP...")
    
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        if "GZipMiddleware" in content and "add_middleware(GZipMiddleware" in content:
            print("  ✅ GZipMiddleware configurado en main.py")
            return True
        else:
            print("  ❌ GZipMiddleware NO encontrado")
            return False
    except Exception as e:
        print(f"  ⚠️ No se pudo verificar: {e}")
        return False

async def analyze_table_stats():
    """Muestra estadísticas de las tablas principales."""
    setup_database_engine()
    from database.database import engine as db_engine
    
    print("\n📊 Estadísticas de base de datos...")
    
    async with db_engine.connect() as conn:
        # Contar registros
        tables = ['productos', 'categorias', 'ordenes', 'variantes_productos', 'wishlist_items']
        
        for table in tables:
            try:
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table};"))
                count = result.scalar()
                print(f"  📦 {table}: {count} registros")
            except Exception as e:
                print(f"  ⚠️ {table}: Error al contar - {e}")
        
        # Tamaño de tablas
        print("\n💽 Tamaño de tablas:")
        result = await conn.execute(text("""
            SELECT 
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 5;
        """))
        
        for row in result:
            print(f"  💾 {row[0]}: {row[1]}")

async def main():
    """Ejecuta todas las verificaciones."""
    print("=" * 70)
    print("🚀 VERIFICACIÓN DE OPTIMIZACIONES DE RENDIMIENTO")
    print("=" * 70)
    
    results = {
        "indexes": await verify_indexes(),
        "cache": await check_cache_service(),
        "gzip": await check_gzip_middleware(),
    }
    
    await test_query_performance()
    await analyze_table_stats()
    
    print("\n" + "=" * 70)
    print("📋 RESUMEN DE VERIFICACIÓN")
    print("=" * 70)
    
    all_passed = all(results.values())
    
    print(f"✅ Índices: {'OK' if results['indexes'] else 'FALTA'}")
    print(f"✅ Cache Redis: {'OK' if results['cache'] else 'FALTA'}")
    print(f"✅ GZIP: {'OK' if results['gzip'] else 'FALTA'}")
    
    if all_passed:
        print("\n🎉 TODAS LAS OPTIMIZACIONES ESTÁN ACTIVAS")
        print("💨 Tu aplicación debería estar SÚPER RÁPIDA")
    else:
        print("\n⚠️ ALGUNAS OPTIMIZACIONES FALTAN")
        print("📖 Revisa OPTIMIZACIONES_RENDIMIENTO.md para más detalles")
    
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
