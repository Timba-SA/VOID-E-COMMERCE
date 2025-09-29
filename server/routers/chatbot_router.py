from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from schemas import chatbot_schemas
from services import ia_services as ia_service
from database.database import get_db
from database.models import ConversacionIA

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONTEXT_TURNS_LIMIT = 5


async def _handle_chat_exception(
    e: Exception,
    conversacion: ConversacionIA,
    db: AsyncSession,
    detail: str,
    status_code: int = 500
):
    error_msg = f"{detail}: {e}"
    logger.error(error_msg, exc_info=True)
    conversacion.respuesta = f"ERROR: {error_msg}"
    db.add(conversacion)
    await db.commit()
    raise HTTPException(status_code=status_code, detail=detail)


@router.post("/query", response_model=chatbot_schemas.ChatResponse)
async def handle_chat_query(query: chatbot_schemas.ChatQuery, db: AsyncSession = Depends(get_db)):
    nueva_conversacion = ConversacionIA(
        sesion_id=query.sesion_id,
        prompt=query.pregunta,
        respuesta=""
    )
    db.add(nueva_conversacion)
    await db.commit()
    await db.refresh(nueva_conversacion)

    try:
        result = await db.execute(
            select(ConversacionIA)
            .filter(ConversacionIA.sesion_id == query.sesion_id)
            .order_by(ConversacionIA.creado_en)
        )
        full_db_history = result.scalars().all()
        limited_history = full_db_history[-(CONTEXT_TURNS_LIMIT * 2):]

        catalog_context = await ia_service.get_catalog_from_db(db)
        system_prompt = ia_service.get_chatbot_system_prompt()

        # ¡ACÁ ESTÁ LA CLAVE! Llamamos a la función correcta
        respuesta_ia = await ia_service.get_ia_response(
            system_prompt=system_prompt,
            catalog_context=catalog_context,
            chat_history=limited_history
        )

        nueva_conversacion.respuesta = respuesta_ia
        db.add(nueva_conversacion)
        await db.commit()

        return chatbot_schemas.ChatResponse(respuesta=respuesta_ia)

    except ia_service.OpenRouterServiceError as e:
        await _handle_chat_exception(
            e, nueva_conversacion, db,
            detail="Error en el servicio de IA (OpenRouter).",
            status_code=503
        )
    except Exception as e:
        await _handle_chat_exception(
            e, nueva_conversacion, db,
            detail="Error interno en el chatbot.",
            status_code=500
        )