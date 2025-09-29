from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from typing import List

from schemas import admin_schemas # Reutilizamos el schema de Orden
from database.database import get_db
from database.models import Orden
from services.auth_services import get_current_user # Usamos el servicio de usuario normal
from schemas.user_schemas import UserOut # Para el tipado de get_current_user

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
    return orders
