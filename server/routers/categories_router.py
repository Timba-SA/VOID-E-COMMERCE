# En server/routers/categories_router.py
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import json
from database.models import Categoria
from services import cache_service
from schemas import product_schemas # Usamos el schema que acabamos de crear
from database.database import get_db

router = APIRouter(
    prefix="/api/categories",
    tags=["Categories"]
)

@router.get("/", response_model=List[product_schemas.Categoria], summary="Obtener todas las categorías")
async def get_all_categories(response: Response, db: AsyncSession = Depends(get_db)):
    """
    Devuelve una lista de todas las categorías de productos con cache ultra-rápido.
    TTL: 15 minutos (las categorías cambian muy poco)
    """
    cache_key = "categories:all"
    
    # Intentar desde cache (versión síncrona)
    cached_data = cache_service.get_cache(cache_key)
    if cached_data:
        response.headers["X-Cache-Status"] = "HIT"
        try:
            return json.loads(cached_data)
        except:
            pass
    
    response.headers["X-Cache-Status"] = "MISS"
    
    # Query optimizada con orden
    result = await db.execute(select(Categoria).order_by(Categoria.nombre))
    categories = result.scalars().all()

    # Convertir y cachear por 15 minutos
    categories_data = [
        product_schemas.Categoria.model_validate(cat).model_dump() for cat in categories
    ]
    cache_service.set_cache(cache_key, json.dumps(categories_data, default=str), ttl=900)

    return categories