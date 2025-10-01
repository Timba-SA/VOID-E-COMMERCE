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
    """Maneja una nueva consulta del usuario al chatbot."""
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

        # Obtenemos el catálogo y el prompt del sistema desde el servicio
        catalog_context = await ia_service.get_catalog_from_db(db)
        system_prompt = ia_service.get_chatbot_system_prompt()

        # Llamamos al servicio de IA (que ahora usa Groq por dentro)
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

    # --- ACÁ ESTÁ EL CAMBIO PRINCIPAL ---
    # ANTES: except ia_service.OpenRouterServiceError as e:
    except ia_service.IAServiceError as e: # AHORA: Usamos el nuevo nombre de la excepción
        await _handle_chat_exception(
            e, nueva_conversacion, db,
            # Y actualizamos el mensaje para que sea más genérico
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