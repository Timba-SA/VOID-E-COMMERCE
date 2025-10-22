# ==========================================
#  IMPORTS ORDENADOS Y CORREGIDOS
# ==========================================
from typing import List, Optional
import json
import hashlib

# Terceros (FastAPI, SQLAlchemy, etc.)
from fastapi import (
    APIRouter, Depends, HTTPException, Query, status,
    File, UploadFile, Form, Response
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.orm.attributes import flag_modified

# Módulos de tu aplicación
from database.database import get_db
from database.models import VarianteProducto, Producto
from schemas import product_schemas, user_schemas
from services import auth_services, cloudinary_service, cache_service


router = APIRouter(
    prefix="/api/products",
    tags=["Products"]
)

# Cache helper para generar keys únicas
def generate_cache_key(prefix: str, **kwargs) -> str:
    """Genera una key única para cache basada en parámetros."""
    key_parts = [prefix]
    for k, v in sorted(kwargs.items()):
        if v is not None:
            key_parts.append(f"{k}:{v}")
    key_string = "|".join(key_parts)
    return f"products:{hashlib.md5(key_string.encode()).hexdigest()}"

@router.get("/", response_model=List[product_schemas.Product], summary="Obtener una lista filtrada de productos")
async def get_products(
    response: Response,
    db: AsyncSession = Depends(get_db),
    q: Optional[str] = Query(None, description="Término de búsqueda para nombre"),
    precio_min: Optional[float] = Query(None, ge=0),
    precio_max: Optional[float] = Query(None, ge=0),
    categoria_id: Optional[str] = Query(None, description="IDs de categoría separados por comas (ej: 1,3,5)"),
    talle: Optional[str] = Query(None, description="Talles separados por comas (ej: S,M,L)"),
    color: Optional[str] = Query(None, description="Colores separados por comas (ej: Negro,Azul)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(12, ge=1, le=500),
    sort_by: Optional[str] = Query(None, description="Opciones: precio_asc, precio_desc, nombre_asc, nombre_desc")
):
    # Generar cache key única para esta consulta
    cache_key = generate_cache_key(
        "list",
        q=q, precio_min=precio_min, precio_max=precio_max,
        categoria_id=categoria_id, talle=talle, color=color,
        skip=skip, limit=limit, sort_by=sort_by
    )
    
    # Intentar obtener desde cache (5 minutos de TTL)
    cached_data = cache_service.get_cache(cache_key)
    if cached_data:
        response.headers["X-Cache-Status"] = "HIT"
        return json.loads(cached_data)
    
    response.headers["X-Cache-Status"] = "MISS"
    
    # Usar selectinload para cargar variantes de forma más eficiente
    query = select(Producto).options(selectinload(Producto.variantes))

    # Filtros sobre el producto principal (no cambian)
    if q: query = query.filter(Producto.nombre.ilike(f"%{q}%"))
    if precio_min is not None: query = query.where(Producto.precio >= precio_min)
    if precio_max is not None: query = query.where(Producto.precio <= precio_max)

    if categoria_id:
        try:
            id_list = [int(i.strip()) for i in categoria_id.split(',')]
            query = query.where(Producto.categoria_id.in_(id_list))
        except ValueError:
            raise HTTPException(status_code=400, detail="El formato de 'categoria_id' es inválido. Deben ser números separados por comas.")

    # --- ¡ACÁ ESTÁ EL ARREGLO PARA LOS FILTROS DE VARIANTES! ---
    # Ahora cada filtro de variante se aplica de forma independiente.
    
    if talle:
        talles = [t.strip() for t in talle.split(',')]
        # Le pedimos productos que tengan CUALQUIER variante que coincida con los talles.
        query = query.where(Producto.variantes.any(VarianteProducto.tamanio.in_(talles)))

    if color:
        colors = [c.strip().lower() for c in color.split(',')]
        # Y que también tengan CUALQUIER variante que coincida con los colores.
        query = query.where(Producto.variantes.any(func.lower(VarianteProducto.color).in_(colors)))

    # El ordenamiento no cambia
    if sort_by:
        if sort_by == "precio_asc": query = query.order_by(Producto.precio.asc())
        elif sort_by == "precio_desc": query = query.order_by(Producto.precio.desc())
        elif sort_by == "nombre_asc": query = query.order_by(Producto.nombre.asc())
        elif sort_by == "nombre_desc": query = query.order_by(Producto.nombre.desc())

    # La paginación y ejecución no cambian
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    products = result.scalars().unique().all()
    
    # Convertir a dict para cachear
    products_data = [product_schemas.Product.model_validate(p).model_dump() for p in products]
    
    # Guardar en cache (300 segundos = 5 minutos)
    cache_service.set_cache(cache_key, json.dumps(products_data, default=str), ttl=300)
    
    return products

# =================================================================
#  EL RESTO DE LAS FUNCIONES (GET POR ID, POST, PUT, DELETE)
#  QUEDAN EXACTAMENTE IGUALES, NO LAS TOQUÉ PARA NO ROMPER NADA.
# =================================================================

@router.get("/{product_id}", response_model=product_schemas.Product, summary="Obtener un producto por su ID")
async def get_product_by_id(
    product_id: int,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    # Cache individual por producto
    cache_key = f"products:detail:{product_id}"
    cached_data = cache_service.get_cache(cache_key)
    
    if cached_data:
        response.headers["X-Cache-Status"] = "HIT"
        return json.loads(cached_data)
    
    response.headers["X-Cache-Status"] = "MISS"
    
    query = select(Producto).options(
        selectinload(Producto.variantes)
    ).where(Producto.id == product_id)

    result = await db.execute(query)
    product = result.scalars().unique().first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {product_id} no encontrado"
        )
    
    # Cachear por 10 minutos
    product_data = product_schemas.Product.model_validate(product).model_dump()
    cache_service.set_cache(cache_key, json.dumps(product_data, default=str), ttl=600)
    
    return product

@router.post("/", response_model=product_schemas.Product, status_code=status.HTTP_201_CREATED, summary="Crear un nuevo producto (Solo Admins)")
async def create_product(
    nombre: str = Form(...),
    descripcion: Optional[str] = Form(None),
    descripcion_i18n: Optional[str] = Form(None),
    precio: float = Form(...),
    sku: str = Form(...),
    stock: int = Form(...),
    categoria_id: int = Form(...),
    material: Optional[str] = Form(None),
    talle: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    images: List[UploadFile] = File(..., description="Hasta 3 imágenes del producto"),
    db: AsyncSession = Depends(get_db),
    current_admin: user_schemas.UserOut = Depends(auth_services.get_current_admin_user)
):
    existing_product_sku = await db.execute(select(Producto).filter(Producto.sku == sku))
    if existing_product_sku.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Ya existe un producto con el SKU: {sku}")

    if len(images) > 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Se pueden subir como máximo 3 imágenes.")

    image_urls = []
    if images and images[0].filename:
        image_urls = await cloudinary_service.upload_images(images)

    # Parseamos el JSON de descripcion_i18n si existe
    import json
    descripcion_i18n_dict = None
    if descripcion_i18n:
        try:
            descripcion_i18n_dict = json.loads(descripcion_i18n)
        except:
            pass

    product_data = product_schemas.ProductCreate(
        nombre=nombre, descripcion=descripcion, descripcion_i18n=descripcion_i18n_dict,
        precio=precio, sku=sku, stock=stock, categoria_id=categoria_id, 
        material=material, talle=talle, color=color, urls_imagenes=image_urls
    )

    new_product = Producto(**product_data.model_dump())
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)

    if talle and stock > 0:
        default_variant = VarianteProducto(
            producto_id=new_product.id, tamanio=talle,
            color=color or "default", cantidad_en_stock=stock
        )
        db.add(default_variant)
        await db.commit()

    # Invalidar cache de listados de productos
    cache_service.delete_pattern("products:*")
    
    query = select(Producto).options(joinedload(Producto.variantes)).filter(Producto.id == new_product.id)
    result = await db.execute(query)
    created_product = result.scalars().unique().first()
    return created_product

@router.put("/{product_id}", response_model=dict, summary="Actualizar un producto (Solo Admins)")
async def update_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: user_schemas.UserOut = Depends(auth_services.get_current_admin_user),
    nombre: Optional[str] = Form(None),
    descripcion: Optional[str] = Form(None),
    descripcion_i18n: Optional[str] = Form(None),
    precio: Optional[float] = Form(None),
    sku: Optional[str] = Form(None),
    stock: Optional[int] = Form(None),
    categoria_id: Optional[int] = Form(None),
    material: Optional[str] = Form(None),
    talle: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    images_to_delete: Optional[str] = Form(None),
    image_order: Optional[str] = Form(None),
    new_images: Optional[List[UploadFile]] = File(None)
):
    product_db = await db.get(Producto, product_id)
    if not product_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    update_data = {k: v for k, v in {
        "nombre": nombre, "descripcion": descripcion, "precio": precio, "sku": sku,
        "stock": stock, "categoria_id": categoria_id, "material": material,
        "talle": talle, "color": color
    }.items() if v is not None}
    
    # Procesamos descripcion_i18n si se envía
    if descripcion_i18n:
        import json
        try:
            descripcion_i18n_dict = json.loads(descripcion_i18n)
            update_data["descripcion_i18n"] = descripcion_i18n_dict
        except:
            pass
    
    for key, value in update_data.items():
        setattr(product_db, key, value)

    current_image_urls = product_db.urls_imagenes.copy() if product_db.urls_imagenes else []

    if images_to_delete:
        urls_to_delete = [url.strip() for url in images_to_delete.split(',') if url.strip()]
        if urls_to_delete:
            await cloudinary_service.delete_images(urls_to_delete)
            current_image_urls = [url for url in current_image_urls if url not in urls_to_delete]

    if new_images and new_images[0].filename:
        if len(current_image_urls) + len(new_images) > 3:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Un producto no puede tener más de 3 imágenes.")
        new_urls = await cloudinary_service.upload_images(new_images)
        current_image_urls.extend(new_urls)

    if image_order:
        ordered_urls = [url.strip() for url in image_order.split(',')]
        final_urls = [url for url in ordered_urls if url in current_image_urls]
        final_urls.extend([url for url in current_image_urls if url not in final_urls])
        current_image_urls = final_urls

    product_db.urls_imagenes = current_image_urls
    
    flag_modified(product_db, "urls_imagenes")
    
    db.add(product_db)
    await db.commit()
    
    # Invalidar cache de este producto y listados
    cache_service.delete_cache(f"products:detail:{product_id}")
    cache_service.delete_pattern("products:*")
    
    return {"message": "Producto actualizado exitosamente"}


@router.delete("/{product_id}", status_code=status.HTTP_200_OK, summary="Eliminar un producto (Solo Admins)")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: user_schemas.UserOut = Depends(auth_services.get_current_admin_user)
):
    product_db = await db.get(Producto, product_id)
    if not product_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    await db.delete(product_db)
    await db.commit()
    
    # Invalidar cache
    cache_service.delete_cache(f"products:detail:{product_id}")
    cache_service.delete_pattern("products:*")
    
    return {"message": "Producto eliminado exitosamente"}


@router.post("/{product_id}/variants", response_model=product_schemas.VarianteProducto, status_code=status.HTTP_201_CREATED, summary="Añadir una variante a un producto (Solo Admins)")
async def create_variant_for_product(
    product_id: int,
    variant_in: product_schemas.VarianteProductoCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: user_schemas.UserOut = Depends(auth_services.get_current_admin_user)
):
    product = await db.get(Producto, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    variant_data = variant_in.model_dump()
    new_variant = VarianteProducto(producto_id=product_id, **variant_data)
    db.add(new_variant)
    await db.commit()
    await db.refresh(new_variant)
    return new_variant


@router.delete("/variants/{variant_id}", status_code=status.HTTP_200_OK, summary="Eliminar una variante de producto (Solo Admins)")
async def delete_variant(
    variant_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: user_schemas.UserOut = Depends(auth_services.get_current_admin_user)
):
    variant_db = await db.get(VarianteProducto, variant_id)
    if not variant_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variante con ID {variant_id} no encontrada."
        )

    await db.delete(variant_db)
    await db.commit()

    return {"message": "Variante eliminada exitosamente"}