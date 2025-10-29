"""
Script para agregar índices compuestos y optimizaciones avanzadas.
Ejecutar después de optimize_database.py para mejoras adicionales.
"""

import asyncio
from sqlalchemy import text
from database.database import setup_database_engine

async def add_composite_indexes():
    """Agrega índices compuestos para queries complejas."""
    
    setup_database_engine()
    from database.database import engine as db_engine
    
    composite_indexes = [
        # Índice compuesto para búsquedas de productos por categoría y precio
        "CREATE INDEX IF NOT EXISTS idx_productos_categoria_precio ON productos(categoria_id, precio);",
        
        # Índice compuesto para búsquedas de productos por categoría y stock
        "CREATE INDEX IF NOT EXISTS idx_productos_categoria_stock ON productos(categoria_id, stock) WHERE stock > 0;",
        
        # Índice compuesto para órdenes por usuario y estado
        "CREATE INDEX IF NOT EXISTS idx_ordenes_usuario_estado ON ordenes(usuario_id, estado_pago);",
        
        # Índice compuesto para órdenes por fecha y estado (para admin)
        "CREATE INDEX IF NOT EXISTS idx_ordenes_fecha_estado ON ordenes(creado_en DESC, estado_pago) WHERE estado_pago = 'Aprobado';",
        
        # Índice para variantes con stock disponible
        "CREATE INDEX IF NOT EXISTS idx_variantes_disponibles ON variantes_productos(producto_id, cantidad_en_stock) WHERE cantidad_en_stock > 0;",
        
        # Índice GIN para búsqueda full-text en descripciones
        "CREATE INDEX IF NOT EXISTS idx_productos_descripcion_gin ON productos USING gin(to_tsvector('spanish', COALESCE(descripcion, '')));",
        
        # Índice para conversaciones recientes del chatbot
        "CREATE INDEX IF NOT EXISTS idx_conversaciones_recientes ON conversaciones_ia(sesion_id, creado_en DESC);",
    ]
    
    async with db_engine.connect() as conn:
        print("🔧 Agregando índices compuestos avanzados...")
        
        for idx_sql in composite_indexes:
            try:
                await conn.execute(text(idx_sql))
                index_name = idx_sql.split("INDEX IF NOT EXISTS")[1].split("ON")[0].strip()
                print(f"✅ Índice compuesto creado: {index_name}")
            except Exception as e:
                print(f"⚠️ Error al crear índice: {e}")
        
        await conn.commit()
        print("\n🎉 Índices compuestos agregados!")

async def optimize_postgresql_settings():
    """Configura parámetros optimizados de PostgreSQL."""
    
    setup_database_engine()
    from database.database import engine as db_engine
    
    optimizations = [
        # Aumentar memoria para operaciones de ordenamiento
        "SET work_mem = '16MB';",
        
        # Habilitar parallel query execution
        "SET max_parallel_workers_per_gather = 2;",
        
        # Optimizar para lecturas frecuentes
        "SET effective_cache_size = '256MB';",
        
        # Vacuum automático más agresivo
        "ALTER TABLE productos SET (autovacuum_vacuum_scale_factor = 0.1);",
        "ALTER TABLE ordenes SET (autovacuum_vacuum_scale_factor = 0.1);",
        "ALTER TABLE variantes_productos SET (autovacuum_vacuum_scale_factor = 0.1);",
    ]
    
    async with db_engine.connect() as conn:
        print("\n⚙️ Optimizando configuración de PostgreSQL...")
        
        for opt_sql in optimizations:
            try:
                await conn.execute(text(opt_sql))
                print(f"✅ {opt_sql[:50]}...")
            except Exception as e:
                print(f"⚠️ Advertencia: {e}")
        
        await conn.commit()
        print("\n🎉 Configuración optimizada!")

async def create_materialized_views():
    """Crea vistas materializadas para queries frecuentes."""
    
    setup_database_engine()
    from database.database import engine as db_engine
    
    views = [
        # Vista de productos con stock disponible
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_productos_disponibles AS
        SELECT 
            p.id,
            p.nombre,
            p.precio,
            p.categoria_id,
            p.urls_imagenes,
            SUM(v.cantidad_en_stock) as stock_total
        FROM productos p
        LEFT JOIN variantes_productos v ON p.id = v.producto_id
        GROUP BY p.id, p.nombre, p.precio, p.categoria_id, p.urls_imagenes
        HAVING SUM(v.cantidad_en_stock) > 0;
        """,
        
        # Índice en la vista materializada
        "CREATE INDEX IF NOT EXISTS idx_mv_productos_categoria ON mv_productos_disponibles(categoria_id);",
        "CREATE INDEX IF NOT EXISTS idx_mv_productos_precio ON mv_productos_disponibles(precio);",
    ]
    
    async with db_engine.connect() as conn:
        print("\n📊 Creando vistas materializadas...")
        
        for view_sql in views:
            try:
                await conn.execute(text(view_sql))
                print(f"✅ Vista/Índice creado")
            except Exception as e:
                if "already exists" not in str(e):
                    print(f"⚠️ {e}")
        
        await conn.commit()
        
        # Refrescar la vista
        try:
            await conn.execute(text("REFRESH MATERIALIZED VIEW mv_productos_disponibles;"))
            await conn.commit()
            print("✅ Vista materializada refrescada")
        except Exception as e:
            print(f"⚠️ {e}")
        
        print("\n🎉 Vistas materializadas listas!")

async def main():
    """Ejecuta todas las optimizaciones avanzadas."""
    print("=" * 60)
    print("OPTIMIZACIONES AVANZADAS DE RENDIMIENTO")
    print("=" * 60)
    
    await add_composite_indexes()
    await optimize_postgresql_settings()
    await create_materialized_views()
    
    print("\n" + "=" * 60)
    print("✨ TODAS LAS OPTIMIZACIONES COMPLETADAS ✨")
    print("=" * 60)
    print("\n💡 Recomendaciones:")
    print("1. Reiniciar el backend para aplicar cambios")
    print("2. Refrescar vistas materializadas periódicamente")
    print("3. Monitorear rendimiento con: EXPLAIN ANALYZE")

if __name__ == "__main__":
    asyncio.run(main())
