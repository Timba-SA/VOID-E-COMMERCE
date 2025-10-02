# server/routers/utils_router.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct
from typing import List

from database.database import get_db
from database.models import VarianteProducto

router = APIRouter(
    prefix="/api/utils",
    tags=["Utilities"]
)

@router.get("/filters/colors", response_model=List[str], summary="Obtener todos los colores únicos de productos")
async def get_available_colors(db: AsyncSession = Depends(get_db)):
    """
    Devuelve una lista de todos los colores únicos existentes en las variantes de productos.
    """
    result = await db.execute(select(distinct(VarianteProducto.color)))
    colors = result.scalars().all()
    # Devolvemos la lista asegurándonos de que no haya valores nulos o vacíos
    return [color for color in colors if color]