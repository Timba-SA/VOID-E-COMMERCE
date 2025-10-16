"""
Script de diagnóstico completo para verificar el flujo de ventas
"""
import asyncio
import sys
import os
from datetime import datetime

# Agregar el directorio parent al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from database.models import Orden, DetalleOrden, VarianteProducto, Producto
from settings import settings

async def diagnostic_check():
    """Ejecuta un diagnóstico completo del sistema de ventas"""
    print("\n" + "="*80)
    print("🔍 DIAGNÓSTICO COMPLETO DEL SISTEMA DE VENTAS")
    print("="*80 + "\n")
    
    # 1. Verificar configuración
    print("1️⃣ VERIFICANDO CONFIGURACIÓN")
    print("-" * 80)
    print(f"✓ BACKEND_URL: {settings.BACKEND_URL}")
    print(f"✓ FRONTEND_URL: {settings.FRONTEND_URL}")
    print(f"✓ DB_SQL_URI: {settings.DB_SQL_URI[:50]}...")
    print(f"✓ MERCADOPAGO_TOKEN configurado: {'Sí' if settings.MERCADOPAGO_TOKEN else 'NO ❌'}")
    print()
    
    # 2. Conectar a la base de datos
    print("2️⃣ CONECTANDO A LA BASE DE DATOS")
    print("-" * 80)
    try:
        engine = create_async_engine(settings.DB_SQL_URI)
        AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
        print("✓ Conexión exitosa a la base de datos")
        print()
    except Exception as e:
        print(f"❌ ERROR al conectar a la base de datos: {e}")
        return
    
    async with AsyncSessionLocal() as session:
        # 3. Verificar órdenes
        print("3️⃣ VERIFICANDO ÓRDENES EN LA BASE DE DATOS")
        print("-" * 80)
        
        # Contar órdenes totales
        result = await session.execute(select(func.count(Orden.id)))
        total_orders = result.scalar()
        print(f"📊 Total de órdenes: {total_orders}")
        
        # Contar órdenes por estado de pago
        result = await session.execute(
            select(Orden.estado_pago, func.count(Orden.id))
            .group_by(Orden.estado_pago)
        )
        for estado, count in result.all():
            print(f"   - {estado or 'Sin estado'}: {count} órdenes")
        
        # Contar órdenes por método de pago
        result = await session.execute(
            select(Orden.metodo_pago, func.count(Orden.id))
            .group_by(Orden.metodo_pago)
        )
        print(f"\n📊 Órdenes por método de pago:")
        for metodo, count in result.all():
            print(f"   - {metodo or 'Sin método'}: {count} órdenes")
        
        print()
        
        # 4. Mostrar últimas 5 órdenes
        print("4️⃣ ÚLTIMAS 5 ÓRDENES REGISTRADAS")
        print("-" * 80)
        
        result = await session.execute(
            select(Orden)
            .order_by(Orden.creado_en.desc())
            .limit(5)
        )
        orders = result.scalars().all()
        
        if not orders:
            print("⚠️  NO HAY ÓRDENES EN LA BASE DE DATOS")
            print()
            print("🔍 POSIBLES CAUSAS:")
            print("   1. El webhook de Mercado Pago NO se está ejecutando")
            print("   2. El BACKEND_URL no es accesible desde internet")
            print("   3. No has configurado el webhook en Mercado Pago")
            print("   4. Hay un error en el proceso de checkout que causa rollback")
            print()
            print("📝 SIGUIENTE PASO:")
            print("   - Revisa los logs del backend después de hacer una compra")
            print("   - Busca mensajes con emojis: 🔔 💳 ✅ ❌")
            print("   - Si NO ves ningún mensaje, el webhook NO se está llamando")
        else:
            for i, order in enumerate(orders, 1):
                print(f"\n{'='*80}")
                print(f"Orden #{order.id}")
                print(f"{'='*80}")
                print(f"📅 Fecha: {order.creado_en}")
                print(f"👤 Usuario ID: {order.usuario_id}")
                print(f"💰 Monto Total: ${order.monto_total}")
                print(f"📦 Estado: {order.estado}")
                print(f"💳 Estado Pago: {order.estado_pago}")
                print(f"🏦 Método de Pago: {order.metodo_pago}")
                print(f"🆔 Payment ID MP: {order.payment_id_mercadopago}")
                
                # Obtener detalles
                details_result = await session.execute(
                    select(DetalleOrden)
                    .where(DetalleOrden.orden_id == order.id)
                )
                details = details_result.scalars().all()
                print(f"📦 Items en la orden: {len(details)}")
                
                for detail in details:
                    # Obtener info del producto
                    variant_result = await session.execute(
                        select(VarianteProducto)
                        .where(VarianteProducto.id == detail.variante_producto_id)
                    )
                    variant = variant_result.scalars().first()
                    
                    if variant:
                        product_result = await session.execute(
                            select(Producto)
                            .where(Producto.id == variant.producto_id)
                        )
                        product = product_result.scalars().first()
                        
                        if product:
                            print(f"   • {product.nombre} ({variant.color} - {variant.tamanio})")
                            print(f"     Cantidad: {detail.cantidad} x ${detail.precio_en_momento_compra}")
        
        print()
        
        # 5. Verificar stock de productos
        print("5️⃣ VERIFICANDO STOCK DE PRODUCTOS")
        print("-" * 80)
        
        result = await session.execute(
            select(Producto, func.sum(VarianteProducto.cantidad_en_stock))
            .join(VarianteProducto)
            .group_by(Producto.id)
            .limit(5)
        )
        
        print("📦 Stock de primeros 5 productos:")
        for product, total_stock in result.all():
            print(f"   • {product.nombre}: {total_stock} unidades")
        
        print()
    
    await engine.dispose()
    
    # 6. Instrucciones finales
    print("6️⃣ PRÓXIMOS PASOS DE DIAGNÓSTICO")
    print("-" * 80)
    print()
    print("Si NO hay órdenes en la base de datos:")
    print("   1. Revisa los logs del backend durante una compra")
    print("   2. Verifica que veas los mensajes con emojis: 🔔 💳 ✅")
    print("   3. Si NO ves mensajes, el webhook NO se está ejecutando")
    print("   4. Verifica la URL del webhook en Mercado Pago:")
    print(f"      {settings.BACKEND_URL}/api/checkout/webhook")
    print()
    print("Si SÍ hay órdenes pero NO aparecen en el admin:")
    print("   1. Verifica que el usuario esté autenticado como admin")
    print("   2. Prueba el endpoint manualmente:")
    print("      GET /api/admin/sales")
    print("   3. Revisa la consola del navegador por errores")
    print()
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(diagnostic_check())
    except Exception as e:
        print(f"\n❌ ERROR FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
