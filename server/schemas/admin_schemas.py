# En backend/schemas/admin_schemas.py
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import List, Optional

# --- Esquemas para Gastos (Estos estaban bien) ---

class GastoBase(BaseModel):
    descripcion: str
    monto: float
    categoria: str | None = None
    fecha: date

class GastoCreate(GastoBase):
    pass

class Gasto(GastoBase):
    id: int

    class Config:
        from_attributes = True


# --- Esquemas para Ventas y Órdenes (CORREGIDOS) ---

# NUEVO: Este esquema define cada item dentro de una venta
class SaleItemCreate(BaseModel):
    # Cambio Clave: Usamos el ID de la variante, no del producto genérico
    variante_producto_id: int
    cantidad: int

# CORREGIDO: El esquema para crear una venta manual
class ManualSaleCreate(BaseModel):
    # Corregido para consistencia con el modelo de DB
    usuario_id: str
    estado: str
    # Corregido para usar la lista de items con variantes
    items: List[SaleItemCreate]
    # Se elimina el campo 'total', ahora se calcula en el backend por seguridad

# NUEVO: Un esquema para mostrar prolijamente cada item en una orden devuelta
class DetalleOrdenOut(BaseModel):
    variante_producto_id: int
    cantidad: int
    precio_en_momento_compra: float

    class Config:
        from_attributes = True

# NUEVO: Esquema para mostrar información de la variante en el detalle de la orden
class VarianteProductoInfo(BaseModel):
    tamanio: str
    color: str
    producto_nombre: str  # Nombre del producto al que pertenece la variante

    class Config:
        from_attributes = True

# NUEVO: Esquema detallado para cada item de la orden (con info del producto)
class DetalleOrdenDetallado(BaseModel):
    variante_producto_id: int
    cantidad: int
    precio_en_momento_compra: float
    variante_producto: VarianteProductoInfo

    class Config:
        from_attributes = True

# CORREGIDO: El esquema para mostrar una orden
class Orden(BaseModel): # Renombrado de OrdenOut para más claridad
    id: int
    # Corregido para consistencia con el modelo de DB
    usuario_id: str
    monto_total: float
    estado: Optional[str]
    estado_pago: Optional[str]
    creado_en: datetime
    # Corregido para mostrar los detalles de la orden de forma prolija
    detalles: List[DetalleOrdenOut]

    class Config:
        from_attributes = True

# NUEVO: Esquema para el detalle completo de una orden (con info de productos)
class OrdenDetallada(BaseModel):
    id: int
    usuario_id: str
    monto_total: float
    estado: Optional[str]
    estado_pago: Optional[str]
    creado_en: datetime
    detalles: List[DetalleOrdenDetallado]

    class Config:
        from_attributes = True