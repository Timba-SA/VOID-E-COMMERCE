# En backend/services/ia_services.py

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
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
        # Cargamos también la categoría relacionada para mostrarla y usarla en tags
        result = await db.execute(select(Producto).options(selectinload(Producto.categoria)))
        products = result.scalars().all()
        if not products:
            return "No hay productos disponibles en este momento."
        
        catalog_lines = ["--- CATÁLOGO DE PRODUCTOS DISPONIBLES ---"]
        for prod in products:
            category = prod.categoria.nombre if getattr(prod, 'categoria', None) else 'Sin categoría'
            color = prod.color or ''
            talle = prod.talle or ''
            material = prod.material or ''
            descripcion = prod.descripcion or ''

            # Construimos tags normalizados para ayudar las búsquedas por color/talle/categoría
            tags_parts = [str(prod.nombre or ''), category, color, talle, material, descripcion]
            # Normalizamos a minúsculas y unimos en una sola cadena compacta
            tags = ' '.join([p.strip().lower() for p in tags_parts if p and p.strip()])

            catalog_lines.append(
                f"- ID: {prod.id} | Nombre: {prod.nombre} | Categoria: {category} | Color: {color} | Talle: {talle} | Precio: ${prod.precio} | Descripción: {descripcion} | Tags: {tags}"
            )
        catalog_lines.append("--- FIN DEL CATÁLOGO ---")
        return "\n".join(catalog_lines)
    except Exception as e:
        logger.error(f"Error al obtener el catálogo de la DB: {e}")
        return "Error al obtener el catálogo."


async def find_matching_products(db: AsyncSession, query: str, limit: int = 5) -> str:
    """Busca productos cuyos campos (nombre, categoría, color, talle, material, descripción)
    coincidan con las palabras de la consulta. Devuelve un bloque formateado con los matches.
    Esta función hace la comparación en Python sobre los mismos tags normalizados que usa
    `get_catalog_from_db`, lo cual es suficiente para catálogos pequeños y evita depender de
    funciones de DB específicas por dialecto.
    """
    try:
        if not query or not query.strip():
            return ""

        q_tokens = [t.strip().lower() for t in query.split() if t.strip()]
        if not q_tokens:
            return ""

        result = await db.execute(select(Producto).options(selectinload(Producto.categoria)))
        products = result.scalars().all()

        matches = []
        for prod in products:
            category = prod.categoria.nombre if getattr(prod, 'categoria', None) else ''
            color = prod.color or ''
            talle = prod.talle or ''
            material = prod.material or ''
            descripcion = prod.descripcion or ''

            tags_parts = [str(prod.nombre or ''), category, color, talle, material, descripcion]
            tags = ' '.join([p.strip().lower() for p in tags_parts if p and p.strip()])

            # Si alguno de los tokens de la query aparece en los tags, es match
            if any(tok in tags for tok in q_tokens):
                matches.append(f"- ID: {prod.id} | Nombre: {prod.nombre} | Categoria: {category} | Color: {color} | Talle: {talle} | Precio: ${prod.precio}")
                if len(matches) >= limit:
                    break

        return "\n".join(matches)
    except Exception as e:
        logger.exception(f"Error buscando productos coincidentes: {e}")
        return ""

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

def _build_messages_for_groq(system_prompt: str, catalog_context: str, chat_history: List[Any]) -> List[Dict[str, Any]]:
    """Construye la lista de mensajes para enviar a la API de Groq de forma más clara y robusta."""
    messages = [{"role": "system", "content": f"{system_prompt}\n\nContexto del Catálogo Actual:\n{catalog_context}"}]

    for entry in chat_history:
        if hasattr(entry, 'prompt') and hasattr(entry, 'respuesta'):
            # Procesa objetos tipo ConversacionIA de la base de datos
            if entry.prompt:
                messages.append({"role": "user", "content": entry.prompt.strip()})
            if entry.respuesta and not str(entry.respuesta).strip().startswith("ERROR:"):
                messages.append({"role": "assistant", "content": entry.respuesta.strip()})
        elif isinstance(entry, dict) and 'role' in entry and 'content' in entry:
            # Procesa entradas de historial en formato de diccionario
            role = entry['role']
            content = str(entry['content']).strip()
            
            if role == 'assistant' and content.startswith("ERROR:"):
                continue  # Omite las respuestas de error del asistente
            
            if role in ['user', 'assistant']:
                messages.append({"role": role, "content": content})
    
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