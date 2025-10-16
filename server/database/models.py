# En BACKEND/database/models.py

from sqlalchemy import (
    Column, Integer, String, Text, DECIMAL, TIMESTAMP, ForeignKey, Date, JSON
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

# Esta es la "mesa de dibujo" sobre la que creamos nuestros planos (modelos)
Base = declarative_base()


class Categoria(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False, index=True)
    productos = relationship("Producto", back_populates="categoria")


class Producto(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)  # Descripción en español (por compatibilidad)
    descripcion_i18n = Column(JSON, nullable=True)  # {"es": "...", "en": "..."}
    precio = Column(DECIMAL(10, 2), nullable=False)
    sku = Column(String(100), unique=True, nullable=False)
    
    urls_imagenes = Column(JSON, nullable=True)

    material = Column(String(100), nullable=True)
    talle = Column(String(50), nullable=True)
    color = Column(String(50), nullable=True)
    stock = Column(Integer, nullable=False, default=0)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    creado_en = Column(TIMESTAMP, server_default=func.now())
    actualizado_en = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    categoria = relationship("Categoria", back_populates="productos")
    variantes = relationship("VarianteProducto", back_populates="producto", cascade="all, delete-orphan")


class VarianteProducto(Base):
    __tablename__ = "variantes_productos"
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    tamanio = Column(String(10), nullable=False)
    color = Column(String(50), nullable=False)
    cantidad_en_stock = Column(Integer, nullable=False)
    producto = relationship("Producto", back_populates="variantes")
    detalles_orden = relationship("DetalleOrden", back_populates="variante_producto")


class Orden(Base):
    __tablename__ = "ordenes"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(String(255), nullable=False)
    monto_total = Column(DECIMAL(10, 2), nullable=False)
    estado = Column(String(50), nullable=True)
    direccion_envio = Column(JSON, nullable=True)
    metodo_pago = Column(String(50), nullable=True)
    estado_pago = Column(String(50), nullable=True)
    creado_en = Column(TIMESTAMP, server_default=func.now())
    detalles = relationship("DetalleOrden", back_populates="orden")
    payment_id_mercadopago = Column(String(255), unique=True, nullable=True, index=True)


class DetalleOrden(Base):
    __tablename__ = "detalles_orden"
    id = Column(Integer, primary_key=True, index=True)
    orden_id = Column(Integer, ForeignKey("ordenes.id"), nullable=False)
    variante_producto_id = Column(Integer, ForeignKey("variantes_productos.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_en_momento_compra = Column(DECIMAL(10, 2), nullable=False)
    orden = relationship("Orden", back_populates="detalles")
    variante_producto = relationship("VarianteProducto", back_populates="detalles_orden")


class Gasto(Base):
    __tablename__ = "gastos"
    id = Column(Integer, primary_key=True, index=True)
    descripcion = Column(String(255), nullable=False)
    monto = Column(DECIMAL(15, 2), nullable=False)
    categoria = Column(String(100), nullable=True)
    fecha = Column(Date, nullable=False)
    creado_en = Column(TIMESTAMP, server_default=func.now())


class ConversacionIA(Base):
    __tablename__ = "conversaciones_ia"
    id = Column(Integer, primary_key=True, index=True)
    sesion_id = Column(String(255), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    respuesta = Column(Text, nullable=False)
    creado_en = Column(TIMESTAMP, server_default=func.now())


# Modelo para almacenar emails entrantes y su estado de procesamiento por la IA
class EmailTask(Base):
    __tablename__ = "email_tasks"
    id = Column(Integer, primary_key=True, index=True)
    sender_email = Column(String(255), nullable=False, index=True)
    subject = Column(String(512), nullable=True)
    body = Column(Text, nullable=True)
    uid = Column(String(255), nullable=True, index=True)
    status = Column(String(50), nullable=False, default='pending')  # pending, processing, done, failed
    attempts = Column(Integer, nullable=False, default=0)
    response = Column(Text, nullable=True)
    creado_en = Column(TIMESTAMP, server_default=func.now())
    procesado_en = Column(TIMESTAMP, nullable=True)

# ===================================================================
# ¡ACÁ ESTÁ LO NUEVO QUE AGREGAMOS!
# ===================================================================
class WishlistItem(Base):
    __tablename__ = "wishlist_items"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(String(255), nullable=False, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    creado_en = Column(TIMESTAMP, server_default=func.now())

    producto = relationship("Producto")