# En BACKEND/routers/admin_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from datetime import timezone
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


# --- Endpoints de Gastos ---
@router.get("/expenses", response_model=List[admin_schemas.Gasto])
async def get_expenses(db: AsyncSession = Depends(get_db)):
    """
    Obtiene todos los gastos registrados, ordenados por fecha descendente.
    """
    result = await db.execute(
        select(Gasto).order_by(Gasto.fecha.desc())
    )
    expenses = result.scalars().all()
    return expenses

@router.post("/expenses", response_model=admin_schemas.Gasto, status_code=201)
async def create_expense(gasto: admin_schemas.GastoCreate, db: AsyncSession = Depends(get_db)):
    """
    Crea un nuevo gasto en el sistema.
    """
    new_expense = Gasto(**gasto.model_dump())
    db.add(new_expense)
    await db.commit()
    await db.refresh(new_expense)
    return new_expense

@router.delete("/expenses/{expense_id}", status_code=status.HTTP_200_OK)
async def delete_expense(expense_id: int, db: AsyncSession = Depends(get_db)):
    """
    Elimina un gasto por su ID.
    """
    result = await db.execute(select(Gasto).where(Gasto.id == expense_id))
    expense = result.scalar_one_or_none()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gasto no encontrado"
        )
    
    await db.delete(expense)
    await db.commit()
    
    return {"message": "Gasto eliminado exitosamente"}


# --- Endpoints de Ventas ---
@router.get("/sales")
async def get_sales(db: AsyncSession = Depends(get_db)):
    """
    Obtiene todas las órdenes del sistema, ordenadas por fecha descendente.
    """
    try:
        result = await db.execute(
            select(Orden)
            .options(joinedload(Orden.detalles))
            .order_by(Orden.creado_en.desc())
        )
        sales = result.scalars().unique().all()
        
        # Convertir objetos ORM a diccionarios y formatear fechas
        orders_list = []
        for order in sales:
            # Asegurar que creado_en sea timezone-aware y convertir a ISO string
            created_at = order.creado_en
            if created_at is not None:
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                else:
                    created_at = created_at.astimezone(timezone.utc)
                created_at_str = created_at.isoformat()
            else:
                created_at_str = None
            
            # Crear diccionario de la orden
            order_dict = {
                "id": order.id,
                "usuario_id": order.usuario_id,
                "monto_total": float(order.monto_total),
                "estado": order.estado,
                "estado_pago": order.estado_pago,
                "creado_en": created_at_str,
                "detalles": []
            }
            
            # Agregar detalles
            for detalle in order.detalles:
                detalle_dict = {
                    "variante_producto_id": detalle.variante_producto_id,
                    "cantidad": detalle.cantidad,
                    "precio_en_momento_compra": float(detalle.precio_en_momento_compra)
                }
                order_dict["detalles"].append(detalle_dict)
            
            orders_list.append(order_dict)
        
        return orders_list
    except Exception as e:
        # Log del error para debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al obtener órdenes: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener órdenes: {str(e)}"
        )

@router.get("/sales/{order_id}", summary="Obtener detalle de una orden específica")
async def get_sale_by_id(order_id: int, db: AsyncSession = Depends(get_db)):
    """
    Obtiene el detalle completo de una orden específica, incluyendo información de los productos.
    """
    try:
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
        
        # Convertir creado_en a UTC timezone-aware y luego a ISO string
        creado_en_utc = order.creado_en
        if creado_en_utc.tzinfo is None:
            creado_en_utc = creado_en_utc.replace(tzinfo=timezone.utc)
        
        # Construimos el objeto de respuesta manualmente para incluir el nombre del producto
        order_dict = {
            "id": order.id,
            "usuario_id": order.usuario_id,
            "monto_total": float(order.monto_total),
            "estado": order.estado,
            "estado_pago": order.estado_pago,
            "creado_en": creado_en_utc.isoformat(),  # Convertir a ISO string
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
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al obtener detalle de orden {order_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener detalle de orden: {str(e)}"
        )

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
    """
    Obtiene las ventas totales agrupadas por fecha.
    Solo incluye órdenes con estado_pago = 'Aprobado'.
    """
    sales_data = await db.execute(
        select(
            func.date(Orden.creado_en).label("fecha"),
            func.sum(Orden.monto_total).label("total")
        )
        .where(Orden.estado_pago == "Aprobado")
        .group_by(func.date(Orden.creado_en))
        .order_by(func.date(Orden.creado_en))
    )
    
    rows = sales_data.all()
    result = [
        metrics_schemas.SalesDataPoint(fecha=row.fecha, total=float(row.total)) 
        for row in rows
    ]
    
    return metrics_schemas.SalesOverTimeChart(data=result)

@router.get("/charts/expenses-by-category", response_model=metrics_schemas.ExpensesByCategoryChart)
async def get_expenses_by_category(db: AsyncSession = Depends(get_db)):
    """
    Obtiene los gastos totales agrupados por categoría.
    Retorna array vacío si no hay gastos registrados.
    """
    expenses_data = await db.execute(
        select(
            Gasto.categoria,
            func.sum(Gasto.monto).label("monto")
        )
        .group_by(Gasto.categoria)
        .order_by(func.sum(Gasto.monto).desc())
    )
    
    rows = expenses_data.all()
    result = [
        metrics_schemas.ExpensesByCategoryDataPoint(categoria=row.categoria, monto=float(row.monto)) 
        for row in rows
    ]
    
    return metrics_schemas.ExpensesByCategoryChart(data=result)

# --- NUEVOS ENDPOINTS DE GRÁFICOS ---

@router.get("/charts/sales-by-category", response_model=metrics_schemas.SalesByCategoryChart)
async def get_sales_by_category(db: AsyncSession = Depends(get_db)):
    """
    Obtiene las ventas totales por categoría de producto (para gráfico de torta).
    Solo considera órdenes con estado_pago = 'Aprobado'.
    """
    # Query compleja que une órdenes -> detalles -> variantes -> productos -> categorías
    sales_by_category_data = await db.execute(
        select(
            Categoria.nombre.label("categoria"),
            func.sum(DetalleOrden.precio_en_momento_compra * DetalleOrden.cantidad).label("total_vendido")
        )
        .select_from(Orden)
        .join(DetalleOrden, Orden.id == DetalleOrden.orden_id)
        .join(VarianteProducto, DetalleOrden.variante_producto_id == VarianteProducto.id)
        .join(Producto, VarianteProducto.producto_id == Producto.id)
        .join(Categoria, Producto.categoria_id == Categoria.id)
        .where(Orden.estado_pago == "Aprobado")
        .group_by(Categoria.nombre)
        .order_by(func.sum(DetalleOrden.precio_en_momento_compra * DetalleOrden.cantidad).desc())
    )
    
    rows = sales_by_category_data.all()
    total_general = sum(float(row.total_vendido) for row in rows)
    
    result = [
        metrics_schemas.SalesByCategoryDataPoint(
            categoria=row.categoria,
            total_vendido=float(row.total_vendido),
            porcentaje=round((float(row.total_vendido) / total_general * 100), 2) if total_general > 0 else 0
        )
        for row in rows
    ]
    
    return metrics_schemas.SalesByCategoryChart(data=result)

@router.get("/charts/top-products", response_model=metrics_schemas.TopProductsChart)
async def get_top_products(db: AsyncSession = Depends(get_db), limit: int = 5):
    """
    Obtiene el top N de productos más vendidos (por cantidad).
    Solo considera órdenes con estado_pago = 'Aprobado'.
    """
    top_products_data = await db.execute(
        select(
            Producto.nombre.label("nombre_producto"),
            func.sum(DetalleOrden.cantidad).label("cantidad_vendida"),
            func.sum(DetalleOrden.precio_en_momento_compra * DetalleOrden.cantidad).label("ingresos_totales")
        )
        .select_from(Orden)
        .join(DetalleOrden, Orden.id == DetalleOrden.orden_id)
        .join(VarianteProducto, DetalleOrden.variante_producto_id == VarianteProducto.id)
        .join(Producto, VarianteProducto.producto_id == Producto.id)
        .where(Orden.estado_pago == "Aprobado")
        .group_by(Producto.nombre)
        .order_by(func.sum(DetalleOrden.cantidad).desc())
        .limit(limit)
    )
    
    result = [
        metrics_schemas.TopProductDataPoint(
            nombre_producto=row.nombre_producto,
            cantidad_vendida=int(row.cantidad_vendida),
            ingresos_totales=float(row.ingresos_totales)
        )
        for row in top_products_data.all()
    ]
    
    return metrics_schemas.TopProductsChart(data=result)

@router.get("/charts/user-activity", response_model=metrics_schemas.UserActivityChart)
async def get_user_activity(db: Database = Depends(get_db_nosql)):
    """
    Obtiene la actividad de usuarios (registros por día) en los últimos 30 días.
    Los datos vienen de MongoDB.
    """
    from datetime import datetime, timedelta
    
    # Fecha de hace 30 días
    fecha_inicio = datetime.now() - timedelta(days=30)
    
    # Agregación en MongoDB para agrupar usuarios por fecha de creación
    pipeline = [
        {
            "$match": {
                "created_at": {"$gte": fecha_inicio}
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$created_at"
                    }
                },
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]
    
    cursor = db.users.aggregate(pipeline)
    results = await cursor.to_list(length=None)
    
    result = [
        metrics_schemas.UserActivityDataPoint(
            fecha=datetime.strptime(item["_id"], "%Y-%m-%d").date(),
            nuevos_usuarios=item["count"]
        )
        for item in results
    ]
    
    return metrics_schemas.UserActivityChart(data=result)

# --- FIN DE NUEVOS ENDPOINTS ---

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
    Acepta nombre (para compatibilidad) y nombre_i18n (para traducciones).
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
    
    new_category = Categoria(
        nombre=category_data.nombre,
        nombre_i18n=category_data.nombre_i18n
    )
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    
    # Invalidar el caché de categorías
    cache_service.delete_cache("categories:all")
    
    return new_category

@router.put("/categories/{category_id}")
async def update_category(
    category_id: int,
    category_data: product_schemas.CategoriaUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza una categoría existente.
    Permite actualizar nombre y/o nombre_i18n.
    """
    try:
        result = await db.execute(select(Categoria).where(Categoria.id == category_id))
        category = result.scalar_one_or_none()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría no encontrada"
            )
        
        # Actualizar campos si se proporcionan
        if category_data.nombre is not None:
            # Verificar que el nuevo nombre no esté en uso por otra categoría
            existing = await db.execute(
                select(Categoria).where(
                    Categoria.nombre == category_data.nombre,
                    Categoria.id != category_id
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe otra categoría con ese nombre"
                )
            category.nombre = category_data.nombre
        
        if category_data.nombre_i18n is not None:
            category.nombre_i18n = category_data.nombre_i18n
        
        await db.commit()
        await db.refresh(category)
        
        # Invalidar el caché de categorías
        cache_service.delete_cache("categories:all")
        
        # Devolver respuesta manual como diccionario
        return {
            "id": category.id,
            "nombre": category.nombre,
            "nombre_i18n": category.nombre_i18n
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al actualizar categoría {category_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar la categoría: {str(e)}"
        )

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
    cache_service.delete_cache("categories:all")
    
    return {"message": "Categoría eliminada exitosamente"}
