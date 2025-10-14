# server/routers/ai_search_router.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from schemas import product_schemas
from services import ia_services
from database.database import get_db
from database.models import Producto

router = APIRouter(prefix="/api/ai-search", tags=["AI Search"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/smart-search", response_model=List[product_schemas.Product], summary="Búsqueda inteligente de productos")
async def smart_product_search_endpoint(
    query: str = Query(..., description="Consulta de búsqueda"),
    limit: int = Query(default=8, ge=1, le=20, description="Número máximo de resultados"),
    db: AsyncSession = Depends(get_db)
):
    """
    Realiza una búsqueda inteligente de productos usando IA para analizar la consulta.
    Incluye análisis de sinónimos, categorías relacionadas y preferencias.
    """
    try:
        search_result = await ia_services.smart_product_search(db, query, limit)
        products = search_result["products"]
        
        logger.info(f"Búsqueda inteligente: '{query}' -> {len(products)} productos encontrados")
        return products
        
    except Exception as e:
        logger.error(f"Error en búsqueda inteligente: {e}")
        return []

@router.get("/recommendations", response_model=List[product_schemas.Product], summary="Recomendaciones personalizadas")
async def get_personalized_recommendations_endpoint(
    session_id: str = Query(..., description="ID de sesión del usuario"),
    limit: int = Query(default=4, ge=1, le=10, description="Número de recomendaciones"),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene recomendaciones personalizadas basadas en el historial de conversaciones del usuario.
    """
    try:
        recommendations = await ia_services.get_personalized_recommendations(db, session_id, limit)
        
        logger.info(f"Recomendaciones para sesión {session_id}: {len(recommendations)} productos")
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generando recomendaciones: {e}")
        return []

@router.post("/analyze-intention", summary="Analizar intención del usuario")
async def analyze_user_intention_endpoint(
    query: str = Query(..., description="Consulta a analizar")
):
    """
    Analiza la intención del usuario en una consulta específica.
    Útil para entender qué tipo de respuesta necesita.
    """
    try:
        intention_analysis = await ia_services.analyze_user_intention(query)
        
        logger.info(f"Análisis de intención: '{query}' -> {intention_analysis['primary_intention']}")
        return {
            "query": query,
            "analysis": intention_analysis,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error analizando intención: {e}")
        return {
            "query": query,
            "analysis": {},
            "success": False,
            "error": str(e)
        }

@router.get("/user-preferences", summary="Obtener preferencias del usuario")
async def get_user_preferences_endpoint(
    session_id: str = Query(..., description="ID de sesión del usuario"),
    db: AsyncSession = Depends(get_db)
):
    """
    Analiza y devuelve las preferencias del usuario basadas en su historial de conversaciones.
    """
    try:
        from sqlalchemy import select
        from database.models import ConversacionIA
        
        # Obtener historial de conversaciones
        result = await db.execute(
            select(ConversacionIA)
            .filter(ConversacionIA.sesion_id == session_id)
            .order_by(ConversacionIA.creado_en.desc())
            .limit(20)
        )
        conversations = result.scalars().all()
        
        preferences = ia_services.analyze_user_preferences(conversations)
        
        logger.info(f"Preferencias para sesión {session_id}: {preferences}")
        return {
            "session_id": session_id,
            "preferences": preferences,
            "total_conversations": len(conversations),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo preferencias: {e}")
        return {
            "session_id": session_id,
            "preferences": {},
            "total_conversations": 0,
            "success": False,
            "error": str(e)
        }