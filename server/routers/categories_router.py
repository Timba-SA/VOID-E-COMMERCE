# En server/routers/categories_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from database.models import Categoria
from schemas import product_schemas # Usamos el schema que acabamos de crear
from database.database import get_db

router = APIRouter(
    prefix="/api/categories",
    tags=["Categories"]
)

@router.get("/", response_model=List[product_schemas.Categoria], summary="Obtener todas las categorías")
async def get_all_categories(db: AsyncSession = Depends(get_db)):
    """
    Devuelve una lista de todas las categorías de productos disponibles en la base de datos.
    """
    result = await db.execute(select(Categoria).order_by(Categoria.nombre))
    categories = result.scalars().all()
    return categories