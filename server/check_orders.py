# Script de diagnóstico para verificar órdenes en la base de datos
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from database.models import Orden, DetalleOrden
from settings import settings

async def check_orders():
    """Verifica las órdenes en la base de datos"""
    engine = create_async_engine(settings.DB_SQL_URI)
    AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # Obtener todas las órdenes
        result = await session.execute(select(Orden))
        orders = result.scalars().all()
        
        print(f"\n{'='*80}")
        print(f"TOTAL DE ÓRDENES EN LA BASE DE DATOS: {len(orders)}")
        print(f"{'='*80}\n")
        
        if not orders:
            print("⚠️  No hay órdenes en la base de datos.")
            print("\nPosibles causas:")
            print("1. El webhook de Mercado Pago no se está ejecutando")
            print("2. El pago no está siendo aprobado")
            print("3. Hay un error en la transacción que causa rollback")
            print("4. La configuración del BACKEND_URL en el webhook es incorrecta")
        else:
            for order in orders:
                print(f"\n📦 Orden #{order.id}")
                print(f"   Usuario ID: {order.usuario_id}")
                print(f"   Monto Total: ${order.monto_total}")
                print(f"   Estado: {order.estado}")
                print(f"   Estado Pago: {order.estado_pago}")
                print(f"   Método de Pago: {order.metodo_pago}")
                print(f"   Payment ID MP: {order.payment_id_mercadopago}")
                print(f"   Creado en: {order.creado_en}")
                
                # Obtener detalles
                details_result = await session.execute(
                    select(DetalleOrden).where(DetalleOrden.orden_id == order.id)
                )
                details = details_result.scalars().all()
                print(f"   Items: {len(details)}")
                for detail in details:
                    print(f"      - Variante {detail.variante_producto_id}: {detail.cantidad} x ${detail.precio_en_momento_compra}")
                print(f"   {'-'*70}")
        
        print(f"\n{'='*80}\n")
    
    await engine.dispose()

if __name__ == "__main__":
    print("\n🔍 Verificando órdenes en la base de datos...")
    try:
        asyncio.run(check_orders())
    except Exception as e:
        print(f"\n❌ Error al verificar órdenes: {e}")
        sys.exit(1)
