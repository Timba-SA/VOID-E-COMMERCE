# En BACKEND/routers/admin_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
# --- ¡IMPORT NUEVO Y CLAVE! ---
from pydantic import TypeAdapter 
# --- FIN DEL IMPORT ---
from schemas import admin_schemas, metrics_schemas, user_schemas, product_schemas
from database.database import get_db, get_db_nosql
from database.models import Gasto, Orden, DetalleOrden, VarianteProducto, Producto, Categoria
from services.auth_services import get_current_admin_user
from services import cache_service
from pymongo.database import Database
from bson import ObjectId
from sqlalchemy.orm import joinedload

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
    dependencies=[Depends(get_current_admin_user)]
)


# --- Endpoints de Gastos (SIN CAMBIOS) ---
@router.get("/expenses", response_model=List[admin_schemas.Gasto])
async def get_expenses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Gasto))
    expenses = result.scalars().all()
    return expenses

@router.post("/expenses", response_model=admin_schemas.Gasto, status_code=201)
async def create_expense(gasto: admin_schemas.GastoCreate, db: AsyncSession = Depends(get_db)):
    new_expense = Gasto(**gasto.model_dump())
    db.add(new_expense)
    await db.commit()
    await db.refresh(new_expense)
    return new_expense


# --- Endpoints de Ventas (SIN CAMBIOS) ---
@router.get("/sales", response_model=List[admin_schemas.Orden])
async def get_sales(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Orden).options(joinedload(Orden.detalles))
    )
    sales = result.scalars().unique().all()
    return sales

@router.get("/sales/{order_id}", response_model=admin_schemas.OrdenDetallada, summary="Obtener detalle de una orden específica")
async def get_sale_by_id(order_id: int, db: AsyncSession = Depends(get_db)):
    """
    Obtiene el detalle completo de una orden específica, incluyendo información de los productos.
    """
    result = await db.execute(
        select(Orden)
        .options(
            joinedload(Orden.detalles)
            .joinedload(DetalleOrden.variante_producto)
            .joinedload(VarianteProducto.producto)
        )
        .where(Orden.id == order_id)
    )
    order = result.scalars().unique().first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orden con ID {order_id} no encontrada"
        )
    
    # Construimos el objeto de respuesta manualmente para incluir el nombre del producto
    order_dict = {
        "id": order.id,
        "usuario_id": order.usuario_id,
        "monto_total": float(order.monto_total),
        "estado": order.estado,
        "estado_pago": order.estado_pago,
        "creado_en": order.creado_en,
        "detalles": []
    }
    
    for detalle in order.detalles:
        detalle_dict = {
            "variante_producto_id": detalle.variante_producto_id,
            "cantidad": detalle.cantidad,
            "precio_en_momento_compra": float(detalle.precio_en_momento_compra),
            "variante_producto": {
                "tamanio": detalle.variante_producto.tamanio,
                "color": detalle.variante_producto.color,
                "producto_nombre": detalle.variante_producto.producto.nombre
            }
        }
        order_dict["detalles"].append(detalle_dict)
    
    return order_dict

@router.post("/sales", status_code=201)
async def create_manual_sale(sale_data: admin_schemas.ManualSaleCreate, db: AsyncSession = Depends(get_db)):
    # ... (código sin cambios)
    total_calculado = 0
    for item in sale_data.items:
        result = await db.execute(
            select(Producto.precio)
            .join(VarianteProducto)
            .where(VarianteProducto.id == item.variante_producto_id)
        )
        precio_producto = result.scalar_one_or_none()
        if not precio_producto:
            raise HTTPException(status_code=404, detail=f"Variante de producto con ID {item.variante_producto_id} no encontrada.")
        total_calculado += float(precio_producto) * item.cantidad

    new_order = Orden(
        usuario_id=sale_data.usuario_id,
        monto_total=total_calculado,
        estado=sale_data.estado,
        estado_pago="pagado"
    )
    db.add(new_order)
    await db.flush()

    for item in sale_data.items:
        result = await db.execute(
            select(Producto.precio)
            .join(VarianteProducto)
            .where(VarianteProducto.id == item.variante_producto_id)
        )
        precio_producto = result.scalar_one()
        
        order_detail = DetalleOrden(
            orden_id=new_order.id,
            variante_producto_id=item.variante_producto_id,
            cantidad=item.cantidad,
            precio_en_momento_compra=precio_producto
        )
        db.add(order_detail)

    await db.commit()
    await db.refresh(new_order)
    return {"message": "Venta manual registrada exitosamente", "order_id": new_order.id}


# --- Endpoints de Usuarios (ACÁ ESTÁ LA SOLUCIÓN DEFINITIVA) ---

@router.get("/users", response_model=List[user_schemas.UserOut])
async def get_users(db: Database = Depends(get_db_nosql)):
    users_cursor = db.users.find({})
    users_list_from_db = await users_cursor.to_list(length=None)
    
    # 1. Creamos un "adaptador" que entiende cómo validar una LISTA de UserOut
    UserListAdapter = TypeAdapter(List[user_schemas.UserOut])
    
    # 2. Usamos el adaptador para validar y transformar la lista entera.
    #    Esto FORZARÁ a Pydantic a aplicar el alias "_id" -> "id" a cada usuario.
    validated_users = UserListAdapter.validate_python(users_list_from_db)
    
    # 3. Devolvemos la lista ya validada y transformada.
    return validated_users


@router.put("/users/{user_id}/role", response_model=user_schemas.UserOut, summary="Actualizar rol de un usuario")
async def update_user_role(user_id: str, user_update: user_schemas.UserUpdateRole, db: Database = Depends(get_db_nosql)):
    # ... (código sin cambios)
    try:
        object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de usuario inválido")

    user = await db.users.find_one({"_id": object_id})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    await db.users.update_one(
        {"_id": object_id},
        {"$set": {"role": user_update.role}}
    )

    updated_user = await db.users.find_one({"_id": object_id})
    return updated_user


# --- Endpoints de Métricas y Gráficos (SIN CAMBIOS) ---
@router.get("/metrics/kpis", response_model=metrics_schemas.KPIMetrics)
async def get_kpis(db: AsyncSession = Depends(get_db), db_nosql: Database = Depends(get_db_nosql)):
    # ... (código sin cambios)
    total_revenue_result = await db.execute(select(func.sum(Orden.monto_total)).where(Orden.estado_pago == "Aprobado"))
    total_revenue = total_revenue_result.scalar_one_or_none() or 0.0
    total_orders_result = await db.execute(select(func.count(Orden.id)).where(Orden.estado_pago == "Aprobado"))
    total_orders = total_orders_result.scalar_one_or_none() or 0
    average_ticket = total_revenue / total_orders if total_orders > 0 else 0.0
    total_users = await db_nosql.users.count_documents({})
    total_expenses_result = await db.execute(select(func.sum(Gasto.monto)))
    total_expenses = total_expenses_result.scalar_one_or_none() or 0.0
    total_products_sold_result = await db.execute(
        select(func.sum(DetalleOrden.cantidad))
        .join(Orden, DetalleOrden.orden_id == Orden.id)
        .where(Orden.estado_pago == "Aprobado")
    )
    total_products_sold = total_products_sold_result.scalar_one_or_none() or 0
    return metrics_schemas.KPIMetrics(
        total_revenue=float(total_revenue),
        average_ticket=float(average_ticket),
        total_orders=total_orders,
        total_users=total_users,
        total_expenses=float(total_expenses),
        total_products_sold=total_products_sold
    )

@router.get("/metrics/products", response_model=metrics_schemas.ProductMetrics)
async def get_product_metrics(db: AsyncSession = Depends(get_db)):
    # ... (código sin cambios)
    most_sold_product_result = await db.execute(
        select(Producto.nombre, func.sum(DetalleOrden.cantidad).label("total_sold"))
        .join(VarianteProducto, Producto.variantes)
        .join(DetalleOrden, VarianteProducto.detalles_orden)
        .group_by(Producto.nombre)
        .order_by(func.sum(DetalleOrden.cantidad).desc())
        .limit(1)
    )
    most_sold_product_data = most_sold_product_result.first()
    most_sold_product_name = most_sold_product_data.nombre if most_sold_product_data else "N/A"
    product_with_most_stock_result = await db.execute(
        select(Producto.nombre)
        .order_by(Producto.stock.desc())
        .limit(1)
    )
    product_with_most_stock_name = product_with_most_stock_result.scalar_one_or_none() or "N/A"
    category_with_most_products_result = await db.execute(
        select(Categoria.nombre, func.count(Producto.id).label("product_count"))
        .join(Producto, Categoria.productos)
        .group_by(Categoria.nombre)
        .order_by(func.count(Producto.id).desc())
        .limit(1)
    )
    category_with_most_products_data = category_with_most_products_result.first()
    category_with_most_products_name = category_with_most_products_data.nombre if category_with_most_products_data else "N/A"
    return metrics_schemas.ProductMetrics(
        most_sold_product=most_sold_product_name,
        product_with_most_stock=product_with_most_stock_name,
        category_with_most_products=category_with_most_products_name
    )

@router.get("/charts/sales-over-time", response_model=metrics_schemas.SalesOverTimeChart)
async def get_sales_over_time(db: AsyncSession = Depends(get_db)):
    # ... (código sin cambios)
    sales_data = await db.execute(
        select(
            func.date(Orden.creado_en).label("fecha"),
            func.sum(Orden.monto_total).label("total")
        )
        .where(Orden.estado_pago == "Aprobado")
        .group_by(func.date(Orden.creado_en))
        .order_by(func.date(Orden.creado_en))
    )
    result = [metrics_schemas.SalesDataPoint(fecha=row.fecha, total=float(row.total)) for row in sales_data.all()]
    return metrics_schemas.SalesOverTimeChart(data=result)

@router.get("/charts/expenses-by-category", response_model=metrics_schemas.ExpensesByCategoryChart)
async def get_expenses_by_category(db: AsyncSession = Depends(get_db)):
    # ... (código sin cambios)
    expenses_data = await db.execute(
        select(
            Gasto.categoria,
            func.sum(Gasto.monto).label("monto")
        )
        .group_by(Gasto.categoria)
        .order_by(func.sum(Gasto.monto).desc())
    )
    result = [metrics_schemas.ExpensesByCategoryDataPoint(categoria=row.categoria, monto=float(row.monto)) for row in expenses_data.all()]
    return metrics_schemas.ExpensesByCategoryChart(data=result)

@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK, summary="Desactivar un usuario (Soft Delete)")
async def deactivate_user(
    user_id: str,
    db: Database = Depends(get_db_nosql)
):
    """
    Realiza un borrado lógico (soft delete) de un usuario, cambiando su estado a inactivo.
    El usuario no podrá iniciar sesión pero sus datos no se eliminarán.
    """
    try:
        object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de usuario inválido")

    result = await db.users.update_one(
        {"_id": object_id},
        {"$set": {"is_active": False}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    return {"message": "Usuario desactivado con éxito."}


# --- Endpoints de Categorías ---
@router.get("/categories", response_model=List[product_schemas.Categoria])
async def get_categories_admin(db: AsyncSession = Depends(get_db)):
    """
    Obtiene todas las categorías para el panel de administración.
    """
    result = await db.execute(select(Categoria).order_by(Categoria.nombre))
    categories = result.scalars().all()
    return categories

@router.post("/categories", response_model=product_schemas.Categoria, status_code=status.HTTP_201_CREATED)
async def create_category(category_data: product_schemas.CategoriaCreate, db: AsyncSession = Depends(get_db)):
    """
    Crea una nueva categoría de productos.
    """
    # Verificar si ya existe una categoría con ese nombre
    existing_category = await db.execute(
        select(Categoria).where(Categoria.nombre == category_data.nombre)
    )
    if existing_category.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una categoría con ese nombre"
        )
    
    new_category = Categoria(nombre=category_data.nombre)
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    
    # Invalidar el caché de categorías
    await cache_service.delete_cache("all_categories")
    
    return new_category

@router.delete("/categories/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)):
    """
    Elimina una categoría. Solo se puede eliminar si no tiene productos asociados.
    """
    result = await db.execute(select(Categoria).where(Categoria.id == category_id))
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    
    # Verificar si tiene productos asociados
    products_result = await db.execute(
        select(func.count(Producto.id)).where(Producto.categoria_id == category_id)
    )
    products_count = products_result.scalar_one()
    
    if products_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede eliminar la categoría porque tiene {products_count} producto(s) asociado(s)"
        )
    
    await db.delete(category)
    await db.commit()
    
    # Invalidar el caché de categorías
    await cache_service.delete_cache("all_categories")
    
    return {"message": "Categoría eliminada exitosamente"}