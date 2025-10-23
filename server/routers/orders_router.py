from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from typing import List, Optional

from schemas import admin_schemas # Reutilizamos el schema de Orden
from database.database import get_db
from database.models import Orden, DetalleOrden, VarianteProducto, Producto
from services.auth_services import get_current_user # Usamos el servicio de usuario normal
from schemas.user_schemas import UserOut # Para el tipado de get_current_user
from datetime import timezone

router = APIRouter(
    prefix="/api/orders",
    tags=["User Orders"],
    dependencies=[Depends(get_current_user)] # Protegemos todo el router
)

@router.get("/me", response_model=List[admin_schemas.Orden], summary="Obtener el historial de órdenes del usuario actual")
async def get_my_orders(db: AsyncSession = Depends(get_db), current_user: UserOut = Depends(get_current_user)):
    """
    Devuelve una lista de todas las órdenes realizadas por el usuario que ha iniciado sesión.
    """
    result = await db.execute(
        select(Orden)
        .options(joinedload(Orden.detalles))
        .where(Orden.usuario_id == str(current_user.id))
        .order_by(Orden.creado_en.desc())
    )
    orders = result.scalars().unique().all()

    # Asegurar que 'creado_en' sea timezone-aware en UTC antes de serializar
    for order in orders:
        try:
            if hasattr(order, 'creado_en') and order.creado_en is not None:
                if order.creado_en.tzinfo is None:
                    order.creado_en = order.creado_en.replace(tzinfo=timezone.utc).isoformat()
                else:
                    order.creado_en = order.creado_en.astimezone(timezone.utc).isoformat()
        except Exception:
            # No bloquear si hay un valor extraño; continuar con el siguiente
            pass

    return orders


@router.get("/me/{order_id}", summary="Obtener detalles completos de una orden específica")
async def get_order_details(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(get_current_user)
):
    """
    Devuelve los detalles completos de una orden específica, incluyendo información de productos y variantes.
    Solo el usuario dueño de la orden puede acceder a esta información.
    """
    result = await db.execute(
        select(Orden)
        .options(
            joinedload(Orden.detalles)
            .joinedload(DetalleOrden.variante_producto)
            .joinedload(VarianteProducto.producto)
        )
        .where(Orden.id == order_id, Orden.usuario_id == str(current_user.id))
    )
    order = result.scalars().first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada o no tienes permiso para verla")
    
    # Construir manualmente la respuesta para evitar problemas de serialización
    detalles_serializados = []
    for detalle in order.detalles:
        detalles_serializados.append({
            "variante_producto_id": detalle.variante_producto_id,
            "cantidad": detalle.cantidad,
            "precio_en_momento_compra": float(detalle.precio_en_momento_compra),
            "variante_producto": {
                "tamanio": detalle.variante_producto.tamanio,
                "color": detalle.variante_producto.color,
                "producto_nombre": detalle.variante_producto.producto.nombre
            }
        })
    
    # Asegurar que creado_en sea timezone-aware en UTC
    try:
        created = order.creado_en
        if created is not None:
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc).isoformat()
            else:
                created = created.astimezone(timezone.utc).isoformat()
    except Exception:
        # Si algo falla, enviar el valor tal cual (podría ser ya string)
        created = order.creado_en if isinstance(order.creado_en, str) else None

    return {
        "id": order.id,
        "usuario_id": order.usuario_id,
        "monto_total": float(order.monto_total),
        "estado": order.estado,
        "estado_pago": order.estado_pago,
        "creado_en": created,
        "direccion_envio": order.direccion_envio,
        "metodo_pago": order.metodo_pago,
        "payment_id_mercadopago": order.payment_id_mercadopago,
        "detalles": detalles_serializados
    }


@router.get("/by-payment/{payment_id}", summary="Buscar orden por payment_id de Mercado Pago")
async def get_order_by_payment_id(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(get_current_user)
):
    """
    Busca una orden específica por su payment_id de Mercado Pago.
    Útil para obtener la orden recién procesada después de un pago.
    Solo devuelve la orden si pertenece al usuario actual.
    """
    result = await db.execute(
        select(Orden)
        .options(joinedload(Orden.detalles))
        .where(
            Orden.payment_id_mercadopago == payment_id,
            Orden.usuario_id == str(current_user.id)
        )
    )
    order = result.scalars().first()
    
    if not order:
        return None  # Retornamos None si no existe (aún no procesada por webhook)
    
    # Asegurar que creado_en sea timezone-aware en UTC antes de devolver
    try:
        if hasattr(order, 'creado_en') and order.creado_en is not None:
            if order.creado_en.tzinfo is None:
                order.creado_en = order.creado_en.replace(tzinfo=timezone.utc).isoformat()
            else:
                order.creado_en = order.creado_en.astimezone(timezone.utc).isoformat()
    except Exception:
        pass
    
    return order
