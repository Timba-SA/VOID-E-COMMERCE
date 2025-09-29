# En backend/services/ia_services.py

import logging
import httpx
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from settings import settings
from database.models import Producto, ConversacionIA

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN PARA OPENROUTER (MISTRAL) ---
API_KEY = settings.OPENROUTER_API_KEY
API_URL = settings.OPENROUTER_API_URL
MODEL_NAME = settings.OPENROUTER_MODEL
SITE_URL = settings.FRONTEND_URL
SITE_NAME = settings.SITE_NAME

class OpenRouterServiceError(Exception):
    pass

# --- Funciones Helper ---
async def get_catalog_from_db(db: AsyncSession) -> str:
    try:
        result = await db.execute(select(Producto))
        products = result.scalars().all()
        if not products: return "No hay productos disponibles en este momento."
        catalog_lines = ["--- CATÁLOGO DE PRODUCTOS DISPONIBLES ---"]
        for prod in products: catalog_lines.append(f"- {prod.nombre} | ${prod.precio} | {prod.descripcion}")
        catalog_lines.append("--- FIN DEL CATÁLOGO ---")
        return "\n".join(catalog_lines)
    except Exception as e:
        logger.error(f"Error al obtener el catálogo de la DB: {e}")
        return "Error al obtener el catálogo."

def get_chatbot_system_prompt() -> str:
    return (
        "Eres Kara, una asistente de ventas experta para la tienda de ropa de alta gama 'VOID'. "
        "Tu personalidad es sofisticada, amable, directa y muy eficiente. Tuteá al cliente. "
        "Tus respuestas deben ser concisas y elegantes (máximo 40 palabras). "
        "Nunca digas que eres una IA. Si te saludan, sé amable y ofrece ayuda. "
        "Usa la información del catálogo que se te proporciona para responder sobre productos. "
        "Si no sabes algo, dilo claramente sin inventar información."
    )

def _build_messages_for_openrouter(system_prompt: str, catalog_context: str, chat_history: List[ConversacionIA]) -> List[Dict[str, Any]]:
    messages = [{"role": "system", "content": system_prompt}]
    
    context_message = (
        "Tengo una tienda y quiero que respondas preguntas sobre mis productos. "
        "Aquí está el catálogo que debes usar exclusivamente:\n"
        f"{catalog_context}"
    )
    messages.append({"role": "user", "content": context_message})
    messages.append({"role": "assistant", "content": "Entendido. Catálogo recibido. Estoy listo para responder preguntas sobre esos productos."})
    
    for entry in chat_history:
        if entry.prompt:
            messages.append({"role": "user", "content": entry.prompt.strip()})
        if entry.respuesta and not entry.respuesta.strip().startswith("ERROR:"):
            messages.append({"role": "assistant", "content": entry.respuesta.strip()})
            
    return messages

async def get_ia_response(system_prompt: str, catalog_context: str, chat_history: List[ConversacionIA]) -> str:
    if not API_KEY:
        raise OpenRouterServiceError("No se encontró la OPENROUTER_API_KEY en el archivo .env")

    headers = { "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}", "Content-Type": "application/json", "HTTP-Referer": settings.FRONTEND_URL, "X-Title": settings.SITE_NAME }
    messages = _build_messages_for_openrouter(system_prompt, catalog_context, chat_history)
    body = { "model": settings.OPENROUTER_MODEL, "messages": messages }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(settings.OPENROUTER_API_URL, headers=headers, json=body, timeout=40)

        if response.status_code != 200:
            logger.error(f"Error de OpenRouter: STATUS={response.status_code}, BODY={response.text}")
            raise OpenRouterServiceError(f"Error {response.status_code}: {response.text}")

        data = response.json()
        
        if data.get("choices") and data["choices"][0].get("message") and data["choices"][0]["message"].get("content"):
            ia_content = data['choices'][0]['message']['content'].strip()
            if ia_content:
                return ia_content

        logger.warning("OpenRouter devolvió una respuesta vacía o con formato inesperado.")
        return "Disculpá, estoy teniendo problemas técnicos para responder en este momento."

    except Exception as e:
        logger.error(f"Error al llamar a OpenRouter: {e}", exc_info=True)
        raise OpenRouterServiceError(f"Error en la comunicación con OpenRouter: {e}")