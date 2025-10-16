# En backend/schemas/product_schemas.py
# ESTE ARCHIVO ES PARA TU BASE DE DATOS SQL (POSTGRESQL, MYSQL, ETC.)

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

# --- Esquemas para Variantes de Producto (SQL) ---
class VarianteProductoBase(BaseModel):
    tamanio: str
    color: str
    cantidad_en_stock: int = Field(..., ge=0)

class VarianteProductoCreate(VarianteProductoBase):
    pass

class VarianteProducto(VarianteProductoBase):
    id: int
    producto_id: int
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas para Productos (SQL) ---
class ProductBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None  # Descripción legacy (español)
    descripcion_i18n: Optional[dict] = None  # {"es": "...", "en": "..."}
    precio: float = Field(..., gt=0)
    sku: str
    urls_imagenes: Optional[List[str]] = []
    material: Optional[str] = None
    stock: int = Field(..., ge=0)
    categoria_id: int

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    nombre: Optional[str] = None
    # ... otros campos opcionales ...

class Product(ProductBase):
    id: int
    variantes: List[VarianteProducto] = []
    model_config = ConfigDict(from_attributes=True)

# --- Esquema para Categorías (SQL) ---
class Categoria(BaseModel):
    id: int
    nombre: str
    model_config = ConfigDict(from_attributes=True)