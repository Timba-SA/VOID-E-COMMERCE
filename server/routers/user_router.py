# En server/routers/user_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database
from typing import List
import uuid # Importamos para generar IDs únicos
from bson import ObjectId  # ⭐ AGREGAR ESTA LÍNEA

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
    print(f"🔍 Buscando direcciones para user_id: {current_user.id}")
    # ⭐ Convertir el string ID a ObjectId
    user_doc = await db.users.find_one({"_id": ObjectId(current_user.id)})
    print(f"📦 Usuario encontrado: {user_doc is not None}")
    if user_doc:
        addresses = user_doc.get("addresses", [])
        print(f"📍 Direcciones encontradas: {len(addresses)}")
        print(f"📋 Contenido: {addresses}")
        return addresses
    print("❌ No se encontró el documento del usuario")
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
    
    print(f"➕ Agregando dirección para user_id: {current_user.id}")
    print(f"📝 Datos de la dirección: {address_dict}")
    
    # ⭐ Convertir el string ID a ObjectId
    result = await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$push": {"addresses": address_dict}}
    )
    
    print(f"✅ Documentos modificados: {result.modified_count}")
    print(f"🔍 Documentos encontrados: {result.matched_count}")
    
    return {"message": "Dirección añadida con éxito", "address_id": address_dict["address_id"]}


@router.put("/addresses/{address_id}", summary="Actualizar una dirección existente")
async def update_address(
    address_id: str,
    address: checkout_schemas.ShippingAddress,
    db: Database = Depends(get_db_nosql),
    current_user: UserOut = Depends(get_current_user)
):
    """Actualiza una dirección de envío específica del usuario."""
    address_dict = address.model_dump()
    address_dict["address_id"] = address_id
    
    print(f"📝 Actualizando dirección con ID: {address_id}")
    print(f"📝 Nuevos datos: {address_dict}")
    
    # ⭐ Convertir el string ID a ObjectId
    result = await db.users.update_one(
        {"_id": ObjectId(current_user.id), "addresses.address_id": address_id},
        {"$set": {"addresses.$": address_dict}}
    )
    
    print(f"✅ Documentos modificados: {result.modified_count}")
    print(f"🔍 Documentos encontrados: {result.matched_count}")
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dirección no encontrada"
        )
    
    return {"message": "Dirección actualizada con éxito"}


@router.delete("/addresses/{address_id}", summary="Eliminar una dirección")
async def delete_address(
    address_id: str,
    db: Database = Depends(get_db_nosql),
    current_user: UserOut = Depends(get_current_user)
):
    """Elimina una dirección de envío específica del usuario."""
    print(f"🗑️ Eliminando dirección con ID: {address_id}")
    
    # ⭐ Convertir el string ID a ObjectId
    result = await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$pull": {"addresses": {"address_id": address_id}}}
    )
    
    print(f"✅ Documentos modificados: {result.modified_count}")
    print(f"🔍 Documentos encontrados: {result.matched_count}")
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dirección no encontrada"
        )
    
    return {"message": "Dirección eliminada con éxito"}