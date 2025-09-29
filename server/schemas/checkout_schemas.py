from pydantic import BaseModel, EmailStr
from typing import Optional
from . import cart_schemas

# --- NUEVO: Molde para la dirección de envío ---
class ShippingAddress(BaseModel):
    firstName: str
    lastName: str
    streetAddress: str
    comments: Optional[str] = None
    city: str
    postalCode: str
    country: str
    state: str
    phone: str

# --- NUEVO: Molde para la petición de preferencia de pago ---
# Ahora el frontend nos enviará el carrito Y la dirección
class PreferenceRequest(BaseModel):
    cart: cart_schemas.Cart
    shipping_address: ShippingAddress

# --- ACTUALIZADO: El pago por API también necesita la dirección ---
class ApiPaymentRequest(BaseModel):
    token: str
    payment_method_id: str
    installments: int
    payer_email: EmailStr
    cart: cart_schemas.Cart
    shipping_address: ShippingAddress # Campo añadido

# --- SIN CAMBIOS ---
class ApiResponse(BaseModel):
    status: str
    message: str
    order_id: Optional[int] = None
    payment_id: Optional[str] = None
