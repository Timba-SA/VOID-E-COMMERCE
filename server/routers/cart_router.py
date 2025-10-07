# En backend/routers/cart_router.py
from fastapi import APIRouter, Depends, HTTPException, Header
from pymongo.database import Database
from typing import Optional
from datetime import datetime
import uuid

from schemas import cart_schemas
from database.database import get_db_nosql
from utils.security import get_current_user_optional

router = APIRouter(
    prefix="/api/cart",
    tags=["Shopping Cart"]
)

# --- Helper para obtener el ID del que hace el pedido ---
def get_session_identifier(current_user: Optional[dict], guest_id: Optional[str]):
    if current_user:
        # --- FIX ---
        # El 'current_user' es el documento de la DB,
        # por lo tanto, usamos '_id' que ya es un ObjectId
        return {"user_id": current_user["_id"]} 
    
    if guest_id:
        return {"guest_session_id": guest_id}
    
    raise HTTPException(status_code=400, detail="Se requiere sesión de usuario o de invitado.")

# --- Helper para convertir ObjectId a str antes de devolver ---
def serialize_cart(cart: dict) -> dict:
    if cart and cart.get("user_id"):
        cart["user_id"] = str(cart["user_id"])
    # El _id es manejado por el alias en Pydantic, no necesita conversión manual aquí
    # si se usa PyObjectId.
    return cart

# --- Endpoint para que el frontend pida un ID de invitado ---
@router.get("/session/guest", summary="Generar un ID de sesión para invitados")
def get_guest_session():
    return {"guest_session_id": str(uuid.uuid4())}

# --- Endpoints del Carrito ---

@router.get("/", response_model=cart_schemas.Cart, summary="Obtener el carrito actual")
async def get_cart(
    guest_session_id: Optional[str] = Header(None, alias="X-Guest-Session-ID"),
    db: Database = Depends(get_db_nosql),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    identifier = get_session_identifier(current_user, guest_session_id)
    cart = await db.carts.find_one(identifier)
    
    if not cart:
        new_cart_data = identifier.copy()
        # Si el identificador es user_id, es un ObjectId, hay que convertirlo
        if "user_id" in new_cart_data:
            new_cart_data["user_id"] = str(new_cart_data["user_id"])
        new_cart_data.update({"items": [], "last_updated": datetime.now()})
        return cart_schemas.Cart(**new_cart_data)
        
    return cart_schemas.Cart(**serialize_cart(cart))

@router.post("/items", response_model=cart_schemas.Cart, summary="Añadir un item al carrito")
async def add_item_to_cart(
    item: cart_schemas.CartItem,
    guest_session_id: Optional[str] = Header(None, alias="X-Guest-Session-ID"),
    db: Database = Depends(get_db_nosql),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    identifier = get_session_identifier(current_user, guest_session_id)
    
    result = await db.carts.update_one(
        {**identifier, "items.variante_id": item.variante_id},
        {"$inc": {"items.$.quantity": item.quantity}}
    )

    if result.modified_count == 0:
        await db.carts.update_one(
            identifier,
            {
                "$push": {"items": item.model_dump()},
                "$set": {"last_updated": datetime.now()}
            },
            upsert=True
        )
        
    updated_cart = await db.carts.find_one(identifier)
    if not updated_cart:
         raise HTTPException(status_code=404, detail="No se pudo encontrar o crear el carrito.")
    return cart_schemas.Cart(**serialize_cart(updated_cart))

# --- ¡ACÁ VA LA NUEVA RUTA MÁGICA! ---
@router.put("/items/{variante_id}", response_model=cart_schemas.Cart, summary="Actualizar la cantidad de un item")
async def update_item_quantity(
    variante_id: int,
    item_update: cart_schemas.CartItemUpdate, # Usa el nuevo schema
    guest_session_id: Optional[str] = Header(None, alias="X-Guest-Session-ID"),
    db: Database = Depends(get_db_nosql),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    identifier = get_session_identifier(current_user, guest_session_id)
    
    # Si la cantidad es 0 o menos, Pydantic ya nos va a tirar un error, ¡joya!
    
    # Buscamos el carrito y el item específico, y le clavamos la nueva cantidad.
    result = await db.carts.update_one(
        {**identifier, "items.variante_id": variante_id},
        {
            "$set": {
                "items.$.quantity": item_update.quantity,
                "last_updated": datetime.now()
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item o carrito no encontrado.")
        
    updated_cart = await db.carts.find_one(identifier)
    return cart_schemas.Cart(**serialize_cart(updated_cart))


@router.delete("/items/{variante_id}", response_model=cart_schemas.Cart, summary="Eliminar un item del carrito")
async def remove_item_from_cart(
    variante_id: int, 
    guest_session_id: Optional[str] = Header(None, alias="X-Guest-Session-ID"),
    db: Database = Depends(get_db_nosql),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    identifier = get_session_identifier(current_user, guest_session_id)
    
    result = await db.carts.update_one(
        identifier,
        {"$pull": {"items": {"variante_id": variante_id}}}
    )
    
    if result.matched_count == 0:
        cart = await db.carts.find_one(identifier)
        if not cart:
            raise HTTPException(status_code=404, detail="Carrito no encontrado.")
    
    updated_cart = await db.carts.find_one(identifier)
    if not updated_cart:
        new_cart_data = identifier.copy()
        if "user_id" in new_cart_data:
            new_cart_data["user_id"] = str(new_cart_data["user_id"])
        new_cart_data.update({"items": [], "last_updated": datetime.now()})
        return cart_schemas.Cart(**new_cart_data)

    return cart_schemas.Cart(**serialize_cart(updated_cart))