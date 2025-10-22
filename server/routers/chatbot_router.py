from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import logging
from typing import Optional

from schemas import chatbot_schemas, user_schemas
from services import ia_services as ia_service
from services import auth_services
from database.database import get_db
from database.models import ConversacionIA, Orden, DetalleOrden, VarianteProducto, Producto

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Límite de turnos de conversación para enviar como contexto a la IA
CONTEXT_TURNS_LIMIT = 5

async def get_user_purchase_history(db: AsyncSession, user_id: str, limit: int = 5) -> str:
    """
    Obtiene el historial de compras del usuario y lo formatea para el contexto de la IA.
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario
        limit: Número máximo de órdenes a incluir
    
    Returns:
        String formateado con el historial de compras
    """
    try:
        # Buscar las últimas órdenes aprobadas del usuario
        result = await db.execute(
            select(Orden)
            .options(
                selectinload(Orden.detalles)
                .selectinload(DetalleOrden.variante_producto)
                .selectinload(VarianteProducto.producto)
            )
            .where(Orden.usuario_id == user_id, Orden.estado_pago == "Aprobado")
            .order_by(Orden.creado_en.desc())
            .limit(limit)
        )
        orders = result.scalars().unique().all()
        
        if not orders:
            return ""
        
        # Formatear el historial
        history_lines = ["\n--- HISTORIAL DE COMPRAS DEL USUARIO ---"]
        
        for order in orders:
            order_date = order.creado_en.strftime("%d/%m/%Y")
            history_lines.append(f"\n📦 Orden #{order.id} - Fecha: {order_date} - Total: ${order.monto_total}")
            
            for detail in order.detalles:
                if detail.variante_producto and detail.variante_producto.producto:
                    product = detail.variante_producto.producto
                    variant = detail.variante_producto
                    history_lines.append(
                        f"   • {product.nombre} "
                        f"(Talle: {variant.tamanio}, Color: {variant.color}) "
                        f"- Cantidad: {detail.cantidad} "
                        f"- Precio: ${detail.precio_en_momento_compra}"
                    )
        
        history_lines.append("--- FIN DEL HISTORIAL DE COMPRAS ---\n")
        return "\n".join(history_lines)
        
    except Exception as e:
        logger.error(f"Error al obtener historial de compras: {e}")
        return ""

async def _handle_chat_exception(
    e: Exception,
    conversacion: ConversacionIA,
    db: AsyncSession,
    detail: str,
    status_code: int = 500
):
    """Función helper para manejar excepciones y guardarlas en la DB."""
    error_msg = f"{detail}: {e}"
    logger.error(error_msg, exc_info=True)
    conversacion.respuesta = f"ERROR: {error_msg}"
    db.add(conversacion)
    await db.commit()
    raise HTTPException(status_code=status_code, detail=detail)


@router.post("/query", response_model=chatbot_schemas.ChatResponse)
async def handle_chat_query(
    query: chatbot_schemas.ChatQuery, 
    db: AsyncSession = Depends(get_db),
    current_user: Optional[user_schemas.UserOut] = Depends(auth_services.get_current_user_optional)
):
    """
    Maneja una nueva consulta del usuario al chatbot con IA mejorada.
    Si el usuario está autenticado, incluye su historial de compras en el contexto.
    """
    # Guardamos el prompt del usuario antes de hacer nada más
    nueva_conversacion = ConversacionIA(
        sesion_id=query.sesion_id,
        prompt=query.pregunta,
        respuesta="" # La respuesta se llenará después
    )
    db.add(nueva_conversacion)
    await db.commit()
    await db.refresh(nueva_conversacion)

    try:
        # Buscamos el historial de la conversación para darle contexto a la IA
        result = await db.execute(
            select(ConversacionIA)
            .filter(ConversacionIA.sesion_id == query.sesion_id)
            .order_by(ConversacionIA.creado_en)
        )
        full_db_history = result.scalars().all()
        # Limitamos el historial para no exceder el límite de tokens
        limited_history = full_db_history[-(CONTEXT_TURNS_LIMIT * 2):]

        # Análisis avanzado de la consulta del usuario
        intention_analysis = await ia_service.analyze_user_intention(query.pregunta)
        logger.info(f"Intención detectada: {intention_analysis['primary_intention']}")

        # Obtener recomendaciones personalizadas basadas en historial
        recommendations = await ia_service.get_personalized_recommendations(db, query.sesion_id, limit=3)
        
        # Obtener catálogo optimizado para la consulta específica
        catalog_context = await ia_service.get_enhanced_catalog_from_db(db, query.pregunta)
        
        # 🆕 NUEVO: Si el usuario está autenticado, obtener su historial de compras
        purchase_history = ""
        if current_user:
            purchase_history = await get_user_purchase_history(db, current_user.id, limit=5)
            if purchase_history:
                logger.info(f"Incluyendo historial de compras para usuario {current_user.id}")
        
        # Si hay recomendaciones personalizadas, agregarlas al contexto
        if recommendations:
            rec_lines = ["\n--- RECOMENDACIONES PERSONALIZADAS ---"]
            for rec in recommendations:
                stock_info = "Sin stock"
                if hasattr(rec, 'variantes') and rec.variantes:
                    total_stock = sum(v.cantidad_en_stock for v in rec.variantes)
                    if total_stock > 0:
                        available_sizes = [v.tamanio for v in rec.variantes if v.cantidad_en_stock > 0]
                        stock_info = f"Stock: {total_stock}"
                        if available_sizes:
                            stock_info += f" | Talles: {', '.join(set(available_sizes))}"
                
                rec_lines.append(
                    f"⭐ ID: {rec.id} | {rec.nombre} | ${rec.precio} | {stock_info}"
                )
            rec_lines.append("--- FIN RECOMENDACIONES ---")
            catalog_context += "\n".join(rec_lines)

        # Búsqueda inteligente para consultas específicas de productos
        if intention_analysis["primary_intention"] == "product_search":
            search_result = await ia_service.smart_product_search(db, query.pregunta, limit=5)
            if search_result["products"]:
                matched_lines = ["\n--- PRODUCTOS RELEVANTES PARA TU BÚSQUEDA ---"]
                for prod in search_result["products"][:4]:  # Limitar a 4 para no sobrecargar
                    stock_info = "Sin stock"
                    if hasattr(prod, 'variantes') and prod.variantes:
                        total_stock = sum(v.cantidad_en_stock for v in prod.variantes)
                        if total_stock > 0:
                            available_sizes = [v.tamanio for v in prod.variantes if v.cantidad_en_stock > 0]
                            stock_info = f"Stock: {total_stock}"
                            if available_sizes:
                                stock_info += f" | Talles: {', '.join(set(available_sizes))}"
                    
                    category = prod.categoria.nombre if getattr(prod, 'categoria', None) else 'Sin categoría'
                    matched_lines.append(
                        f"🎯 ID: {prod.id} | {prod.nombre} | Categoría: {category} | "
                        f"Color: {prod.color or 'N/A'} | ${prod.precio} | {stock_info}"
                    )
                matched_lines.append("--- FIN PRODUCTOS RELEVANTES ---")
                catalog_context = "\n".join(matched_lines) + "\n" + catalog_context

        # 🆕 NUEVO: Agregar el historial de compras al contexto del catálogo
        if purchase_history:
            catalog_context = purchase_history + "\n" + catalog_context

        # Generar prompt personalizado
        user_preferences = ia_service.analyze_user_preferences(limited_history)
        system_prompt = ia_service.get_enhanced_system_prompt(user_preferences, intention_analysis)
        
        # 🆕 NUEVO: Si hay historial de compras, agregar instrucción al sistema
        if purchase_history:
            system_prompt += "\n\nIMPORTANTE: El usuario está autenticado y tienes acceso a su historial de compras. Puedes usarlo para personalizar tus recomendaciones y respuestas. Por ejemplo, si compró algo antes y pregunta por productos similares, puedes mencionarlo."

        # Llamamos al servicio de IA mejorado
        respuesta_ia = await ia_service.get_ia_response(
            system_prompt=system_prompt,
            catalog_context=catalog_context,
            chat_history=limited_history
        )

        # Si todo fue bien, actualizamos la conversación con la respuesta de la IA
        nueva_conversacion.respuesta = respuesta_ia
        db.add(nueva_conversacion)
        await db.commit()

        return chatbot_schemas.ChatResponse(respuesta=respuesta_ia)

    except ia_service.IAServiceError as e:
        await _handle_chat_exception(
            e, nueva_conversacion, db,
            detail="El servicio de IA no está disponible en este momento.",
            status_code=503
        )
    except Exception as e:
        # Este es el "atrapa-todo" por si falla cualquier otra cosa
        await _handle_chat_exception(
            e, nueva_conversacion, db,
            detail="Ocurrió un error interno en el servidor del chatbot.",
            status_code=500
        )