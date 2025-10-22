# server/schemas/checkout_schemas.py

from pydantic import BaseModel, EmailStr
from typing import Optional
from . import cart_schemas

# --- Molde para la dirección de envío ---
class ShippingAddress(BaseModel):
    firstName: str
    lastName: str
    email: Optional[EmailStr] = None  # ⭐ Email del usuario
    streetAddress: str
    comments: Optional[str] = None
    city: str
    postalCode: str
    country: str
    state: str
    prefix: Optional[str] = None  # ⭐ Prefijo telefónico
    phone: str
    address_id: Optional[str] = None  # ⭐ CAMPO NUEVO para identificar direcciones guardadas

# --- ¡ACÁ ESTÁ EL CAMBIO! ---
# Le decimos que la petición ahora también incluye el costo del envío
class PreferenceRequest(BaseModel):
    cart: cart_schemas.Cart
    shipping_address: ShippingAddress
    shipping_cost: float  # <-- LÍNEA NUEVA

# --- El resto queda igual ---
class ApiPaymentRequest(BaseModel):
    token: str
    payment_method_id: str
    installments: int
    payer_email: EmailStr
    cart: cart_schemas.Cart
    shipping_address: ShippingAddress

class ApiResponse(BaseModel):
    status: str
    message: str
    order_id: Optional[int] = None
    payment_id: Optional[str] = None