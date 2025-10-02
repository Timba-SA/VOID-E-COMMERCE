# En backend/services/ia_services.py

import logging
from typing import List, Dict, Any, Optional # <--- CAMBIO 1: Importamos Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from groq import Groq, GroqError

from settings import settings
from database.models import Producto, ConversacionIA

# ... (El resto de la configuración y las funciones helper se mantienen igual) ...

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    client = Groq(api_key=settings.GROQ_API_KEY)
except Exception as e:
    logger.error(f"No se pudo inicializar el cliente de Groq. ¿Falta GROQ_API_KEY en .env? Error: {e}")
    client = None

MODEL_NAME = settings.GROQ_MODEL_NAME

class IAServiceError(Exception):
    """Excepción personalizada para errores del servicio de IA."""
    pass

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
    
    for entry in chat_history:
        if entry.prompt:
            messages.append({"role": "user", "content": entry.prompt.strip()})
        if entry.respuesta and not entry.respuesta.strip().startswith("ERROR:"):
            messages.append({"role": "assistant", "content": entry.respuesta.strip()})
            
    return messages


# --- ¡ACÁ ESTÁ LA MAGIA DEL REFACTOR! ---
async def get_ia_response(
    system_prompt: str,
    catalog_context: str,
    chat_history: Optional[List[ConversacionIA]] = None, # <--- CAMBIO 2: Ahora es opcional
    user_prompt: Optional[str] = None # <--- CAMBIO 3: Nuevo parámetro opcional
) -> str:
    """
    Función principal MEJORADA para ser más flexible.
    Puede recibir un historial de chat completo O un único prompt de usuario.
    """
    if not client:
        raise IAServiceError("El cliente de Groq no está inicializado. Revisa la API Key.")

    # Usamos el historial si existe, si no, partimos de una lista vacía.
    history_to_use = chat_history if chat_history is not None else []
    messages = _build_messages_for_groq(system_prompt, catalog_context, history_to_use)

    # <--- CAMBIO 4: Si nos pasaron un `user_prompt`, lo agregamos al final ---
    # Esto es lo que usará tu worker de emails.
    if user_prompt:
        messages.append({"role": "user", "content": user_prompt})

    # El resto de la función es exactamente igual, no se toca nada.
    try:
        logger.info(f"Enviando petición a Groq con el modelo {MODEL_NAME}...")
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=MODEL_NAME,
            temperature=0.7,
            max_tokens=150,
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