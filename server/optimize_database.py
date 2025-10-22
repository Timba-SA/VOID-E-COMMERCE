"""
Script para agregar índices y optimizaciones a la base de datos.
Ejecutar después de las migraciones principales.
"""

import asyncio
from sqlalchemy import text
from database.database import setup_database_engine, engine

async def add_database_indexes():
    """Agrega índices para mejorar el rendimiento de las consultas."""
    
    setup_database_engine()
    
    # Importar el engine después de configurarlo
    from database.database import engine as db_engine
    
    indexes = [
        # Índices para la tabla productos
        "CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria_id);",
        "CREATE INDEX IF NOT EXISTS idx_productos_precio ON productos(precio);",
        "CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos USING gin(to_tsvector('spanish', nombre));",
        
        # Índices para la tabla ordenes
        "CREATE INDEX IF NOT EXISTS idx_ordenes_usuario ON ordenes(usuario_id);",
        "CREATE INDEX IF NOT EXISTS idx_ordenes_estado_pago ON ordenes(estado_pago);",
        "CREATE INDEX IF NOT EXISTS idx_ordenes_creado_en ON ordenes(creado_en DESC);",
        "CREATE INDEX IF NOT EXISTS idx_ordenes_payment_id ON ordenes(payment_id_mercadopago);",
        
        # Índices para la tabla detalles_orden
        "CREATE INDEX IF NOT EXISTS idx_detalles_orden_orden_id ON detalles_orden(orden_id);",
        "CREATE INDEX IF NOT EXISTS idx_detalles_orden_variante ON detalles_orden(variante_producto_id);",
        
        # Índices para la tabla variantes_productos
        "CREATE INDEX IF NOT EXISTS idx_variantes_producto_id ON variantes_productos(producto_id);",
        "CREATE INDEX IF NOT EXISTS idx_variantes_stock ON variantes_productos(cantidad_en_stock);",
        
        # Índices para la tabla wishlist_items
        "CREATE INDEX IF NOT EXISTS idx_wishlist_usuario ON wishlist_items(usuario_id);",
        "CREATE INDEX IF NOT EXISTS idx_wishlist_producto ON wishlist_items(producto_id);",
        "CREATE INDEX IF NOT EXISTS idx_wishlist_usuario_producto ON wishlist_items(usuario_id, producto_id);",
        
        # Índices para la tabla conversaciones_ia
        "CREATE INDEX IF NOT EXISTS idx_conversaciones_sesion ON conversaciones_ia(sesion_id);",
        "CREATE INDEX IF NOT EXISTS idx_conversaciones_creado ON conversaciones_ia(creado_en DESC);",
        
        # Índices para la tabla gastos
        "CREATE INDEX IF NOT EXISTS idx_gastos_fecha ON gastos(fecha DESC);",
        "CREATE INDEX IF NOT EXISTS idx_gastos_categoria ON gastos(categoria);",
        
        # Índices para la tabla email_tasks
        "CREATE INDEX IF NOT EXISTS idx_email_tasks_status ON email_tasks(status);",
        "CREATE INDEX IF NOT EXISTS idx_email_tasks_sender ON email_tasks(sender_email);",
    ]
    
    async with db_engine.connect() as conn:
        print("🔧 Agregando índices a la base de datos...")
        
        for idx_sql in indexes:
            try:
                await conn.execute(text(idx_sql))
                index_name = idx_sql.split("INDEX IF NOT EXISTS")[1].split("ON")[0].strip()
                print(f"✅ Índice creado/verificado: {index_name}")
            except Exception as e:
                print(f"⚠️ Error al crear índice: {e}")
        
        await conn.commit()
        print("\n🎉 Proceso de optimización completado!")

async def optimize_database():
    """Ejecuta optimizaciones adicionales."""
    
    setup_database_engine()
    
    # Importar el engine después de configurarlo
    from database.database import engine as db_engine
    
    optimizations = [
        # Analizar tablas para actualizar estadísticas
        "ANALYZE productos;",
        "ANALYZE ordenes;",
        "ANALYZE detalles_orden;",
        "ANALYZE variantes_productos;",
        "ANALYZE categorias;",
        "ANALYZE wishlist_items;",
    ]
    
    async with db_engine.connect() as conn:
        print("\n📊 Optimizando estadísticas de tablas...")
        
        for opt_sql in optimizations:
            try:
                await conn.execute(text(opt_sql))
                table_name = opt_sql.split("ANALYZE")[1].strip().rstrip(";")
                print(f"✅ Tabla optimizada: {table_name}")
            except Exception as e:
                print(f"⚠️ Error al optimizar: {e}")
        
        await conn.commit()
        print("\n🎉 Optimización de estadísticas completada!")

async def main():
    """Ejecuta todas las optimizaciones."""
    print("=" * 60)
    print("SCRIPT DE OPTIMIZACIÓN DE BASE DE DATOS")
    print("=" * 60)
    
    await add_database_indexes()
    await optimize_database()
    
    print("\n" + "=" * 60)
    print("PROCESO COMPLETADO EXITOSAMENTE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
