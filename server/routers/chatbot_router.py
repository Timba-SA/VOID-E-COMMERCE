from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from schemas import chatbot_schemas
from services import ia_services as ia_service # Mantenemos este import igual
from database.database import get_db
from database.models import ConversacionIA

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Límite de turnos de conversación para enviar como contexto a la IA
CONTEXT_TURNS_LIMIT = 5

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
async def handle_chat_query(query: chatbot_schemas.ChatQuery, db: AsyncSession = Depends(get_db)):
    """Maneja una nueva consulta del usuario al chatbot con IA mejorada."""
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

        # Generar prompt personalizado
        user_preferences = ia_service.analyze_user_preferences(limited_history)
        system_prompt = ia_service.get_enhanced_system_prompt(user_preferences, intention_analysis)

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