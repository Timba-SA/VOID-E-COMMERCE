# En server/routers/wishlist_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload # ¡Importamos la magia!
from typing import List

from database.database import get_db
from database.models import WishlistItem, Producto
from services.auth_services import get_current_user
from schemas.user_schemas import UserOut
from schemas.product_schemas import Product as ProductSchema

router = APIRouter(
    prefix="/api/wishlist",
    tags=["Wishlist"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/", response_model=List[ProductSchema], summary="Obtener la wishlist del usuario")
async def get_wishlist(
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(get_current_user)
):
    """Devuelve una lista de productos en la wishlist del usuario actual."""
    stmt = select(WishlistItem.producto_id).where(WishlistItem.usuario_id == current_user.id)
    result = await db.execute(stmt)
    product_ids = result.scalars().all()

    if not product_ids:
        return []

    # ¡ACÁ ESTÁ EL ARREGLO! Le decimos que cargue también los detalles (variantes) de cada producto.
    product_stmt = select(Producto).options(joinedload(Producto.variantes)).where(Producto.id.in_(product_ids))
    product_result = await db.execute(product_stmt)
    products = product_result.scalars().unique().all()
    
    return products

@router.post("/{product_id}", status_code=status.HTTP_201_CREATED, summary="Añadir un producto a la wishlist")
async def add_to_wishlist(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(get_current_user)
):
    """Añade un producto a la wishlist del usuario actual."""
    existing_item = await db.execute(
        select(WishlistItem).where(
            WishlistItem.usuario_id == current_user.id,
            WishlistItem.producto_id == product_id
        )
    )
    if existing_item.scalars().first():
        return {"message": "El producto ya está en tu wishlist."}

    product = await db.get(Producto, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")

    new_item = WishlistItem(usuario_id=current_user.id, producto_id=product_id)
    db.add(new_item)
    await db.commit()
    
    return {"message": "Producto añadido a tu wishlist."}

@router.delete("/{product_id}", status_code=status.HTTP_200_OK, summary="Eliminar un producto de la wishlist")
async def remove_from_wishlist(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(get_current_user)
):
    """Elimina un producto de la wishlist del usuario actual."""
    stmt = delete(WishlistItem).where(
        WishlistItem.usuario_id == current_user.id,
        WishlistItem.producto_id == product_id
    )
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado en tu wishlist.")

    return {"message": "Producto eliminado de tu wishlist."}