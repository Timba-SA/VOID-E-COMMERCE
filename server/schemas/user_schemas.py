# En backend/schemas/user_schemas.py

from pydantic import BaseModel, EmailStr, Field, BeforeValidator, ConfigDict
from typing import Optional
from typing_extensions import Annotated
from bson import ObjectId

# --- EL TRADUCTOR MÁGICO ---
PyObjectId = Annotated[str, BeforeValidator(str)]

# --- Tus modelos base (sin cambios) ---
class Phone(BaseModel):
    prefix: str
    number: str

class UserBase(BaseModel):
    email: EmailStr
    name: str
    last_name: str
    phone: Optional[Phone] = None
    role: str = "user"

class UserCreate(UserBase):
    password: str

# --- LA CLASE CORREGIDA ---
class UserOut(UserBase):
    id: PyObjectId = Field(alias="_id")

    model_config = ConfigDict(
        populate_by_name = True,
        arbitrary_types_allowed = True
    )

# --- El resto de tus modelos (sin cambios) ---
class Token(BaseModel):
    access_token: str
    token_type: str

class UserUpdateRole(BaseModel):
    role: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

# --- ¡ACÁ ESTÁ EL AJUSTE! ---
# Sacamos el token de acá porque ya no viaja en el cuerpo del mensaje.
class ResetPasswordRequest(BaseModel):
    new_password: str

class MergeCartRequest(BaseModel):
    guest_session_id: str