# En server/routers/categories_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from database.models import Categoria
from services import cache_service
from schemas import product_schemas # Usamos el schema que acabamos de crear
from database.database import get_db

router = APIRouter(
    prefix="/api/categories",
    tags=["Categories"]
)

@router.get("/", response_model=List[product_schemas.Categoria], summary="Obtener todas las categorías")
async def get_all_categories(db: AsyncSession = Depends(get_db)):
    """
    Devuelve una lista de todas las categorías de productos.
    Primero intenta obtenerlas del caché; si no, las busca en la base de datos.
    """
    # 1. Intentamos leer del caché usando una clave única
    cached_categories = await cache_service.get_cache("all_categories")
    if cached_categories:
        print("¡Respuesta desde CACHÉ! ⚡️")
        # Redis nos devuelve una lista de diccionarios, la convertimos de vuelta a nuestros modelos Pydantic
        return [product_schemas.Categoria.model_validate(cat) for cat in cached_categories]

    # 2. Si no hay nada en el caché, vamos a la base de datos (como antes)
    print("Respuesta desde la BASE DE DATOS... 🐌")
    result = await db.execute(select(Categoria).order_by(Categoria.nombre))
    categories = result.scalars().all()

    # 3. ANTES de devolver la respuesta, la guardamos en el caché para la próxima vez
    if categories:
        # Convertimos la lista de objetos SQLAlchemy a una lista de diccionarios para guardarla
        categories_dict = [
            product_schemas.Categoria.model_validate(cat).model_dump() for cat in categories
        ]
        await cache_service.set_cache("all_categories", categories_dict)

    return categories