# En backend/services/ia_services.py

import logging
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from groq import Groq, GroqError  # Importamos la librería oficial de Groq

from settings import settings
from database.models import Producto, ConversacionIA

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN PARA GROQ (NUEVO Y MEJORADO) ---
# Usamos la librería oficial, que es más limpia y segura.
# Asegúrate de tenerla instalada: pip install groq
try:
    client = Groq(api_key=settings.GROQ_API_KEY)
except Exception as e:
    logger.error(f"No se pudo inicializar el cliente de Groq. ¿Falta GROQ_API_KEY en .env? Error: {e}")
    client = None

MODEL_NAME = settings.GROQ_MODEL_NAME

class IAServiceError(Exception):
    """Excepción personalizada para errores del servicio de IA."""
    pass

# --- Funciones Helper (sin cambios, pero igual de importantes) ---
async def get_catalog_from_db(db: AsyncSession) -> str:
    """Obtiene el catálogo de productos formateado desde la base de datos."""
    try:
        result = await db.execute(select(Producto))
        products = result.scalars().all()
        if not products:
            return "No hay productos disponibles en este momento."
        
        catalog_lines = ["--- CATÁLOGO DE PRODUCTOS DISPONIBLES ---"]
        for prod in products:
            catalog_lines.append(f"- ID: {prod.id} | Nombre: {prod.nombre} | Precio: ${prod.precio} | Descripción: {prod.descripcion}")
        catalog_lines.append("--- FIN DEL CATÁLOGO ---")
        return "\n".join(catalog_lines)
    except Exception as e:
        logger.error(f"Error al obtener el catálogo de la DB: {e}")
        return "Error al obtener el catálogo."

def get_chatbot_system_prompt() -> str:
    """Define la personalidad y las instrucciones base del chatbot."""
    return (
        "Eres Kara, una asistente de ventas experta para la tienda de ropa de alta gama 'VOID Indumentaria'. "
        "Tu personalidad es sofisticada, amable, directa y muy eficiente. Tuteá al cliente. "
        "Tus respuestas deben ser concisas y elegantes (máximo 40-50 palabras). "
        "Nunca digas que eres una IA o un modelo de lenguaje. Eres Kara. "
        "Usa la información del catálogo que se te proporciona para responder sobre productos. "
        "Si no sabes algo, dilo claramente sin inventar información, y ofrece contactar a un humano."
    )

def _build_messages_for_groq(system_prompt: str, catalog_context: str, chat_history: List[ConversacionIA]) -> List[Dict[str, Any]]:
    """Construye la lista de mensajes para enviar a la API de Groq."""
    messages = [{"role": "system", "content": f"{system_prompt}\n\nContexto del Catálogo Actual:\n{catalog_context}"}]
    
    # Agregamos el historial de la conversación actual
    for entry in chat_history:
        if entry.prompt:
            messages.append({"role": "user", "content": entry.prompt.strip()})
        # Solo agregamos respuestas de la IA si fueron exitosas
        if entry.respuesta and not entry.respuesta.strip().startswith("ERROR:"):
            messages.append({"role": "assistant", "content": entry.respuesta.strip()})
            
    return messages

async def get_ia_response(system_prompt: str, catalog_context: str, chat_history: List[ConversacionIA]) -> str:
    """
    Función principal refactorizada para usar el SDK de Groq.
    Es más limpia, más segura y maneja mejor los errores.
    """
    if not client:
        raise IAServiceError("El cliente de Groq no está inicializado. Revisa la API Key.")

    messages = _build_messages_for_groq(system_prompt, catalog_context, chat_history)

    try:
        logger.info(f"Enviando petición a Groq con el modelo {MODEL_NAME}...")
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=MODEL_NAME,
            temperature=0.7, # Un poco de creatividad pero sin que invente cosas
            max_tokens=150,  # Límite de tokens para la respuesta
        )
        
        ia_content = chat_completion.choices[0].message.content.strip()
        
        if ia_content:
            logger.info("Respuesta de Groq recibida exitosamente.")
            return ia_content
        else:
            logger.warning("Groq devolvió una respuesta vacía.")
            return "Disculpá, no pude procesar tu consulta en este momento."

    except GroqError as e:
        logger.error(f"Error específico de la API de Groq: {e}", exc_info=True)
        raise IAServiceError(f"Error en la API de Groq: {e.status_code} - {e.message}")
    except Exception as e:
        logger.error(f"Error inesperado al llamar a Groq: {e}", exc_info=True)
        raise IAServiceError(f"Error inesperado en la comunicación con el servicio de IA.")