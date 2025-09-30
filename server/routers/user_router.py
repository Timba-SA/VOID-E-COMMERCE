# En server/routers/user_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database
from typing import List
import uuid # Importamos para generar IDs únicos

from schemas import checkout_schemas
from database.database import get_db_nosql
from services.auth_services import get_current_user
from schemas.user_schemas import UserOut

router = APIRouter(
    prefix="/api/user",
    tags=["User Profile"],
    dependencies=[Depends(get_current_user)]
)

# --- ENDPOINTS DE PERFIL (Por ahora, solo para obtener datos) ---
@router.get("/profile", response_model=UserOut, summary="Obtener datos del perfil del usuario actual")
async def get_user_profile(current_user: UserOut = Depends(get_current_user)):
    """Devuelve la información del usuario que ha iniciado sesión."""
    return current_user

# --- ENDPOINTS DE DIRECCIONES (¡Acá está la magia nueva!) ---
@router.get("/addresses", response_model=List[checkout_schemas.ShippingAddress], summary="Obtener todas las direcciones guardadas")
async def get_user_addresses(
    db: Database = Depends(get_db_nosql),
    current_user: UserOut = Depends(get_current_user)
):
    """Devuelve una lista de todas las direcciones guardadas por el usuario."""
    user_doc = await db.users.find_one({"_id": current_user.id})
    if user_doc:
        return user_doc.get("addresses", [])
    return []


@router.post("/addresses", status_code=status.HTTP_201_CREATED, summary="Añadir una nueva dirección")
async def add_new_address(
    address: checkout_schemas.ShippingAddress,
    db: Database = Depends(get_db_nosql),
    current_user: UserOut = Depends(get_current_user)
):
    """Añade una nueva dirección de envío al perfil del usuario."""
    address_dict = address.model_dump()
    # Le asignamos un ID único para poder identificarla después
    address_dict["address_id"] = str(uuid.uuid4())
    
    await db.users.update_one(
        {"_id": current_user.id},
        {"$push": {"addresses": address_dict}}
    )
    return {"message": "Dirección añadida con éxito", "address_id": address_dict["address_id"]}