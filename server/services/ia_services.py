# En backend/services/ia_services.py

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from groq import Groq, GroqError
import json

from settings import settings
from database.models import Producto, ConversacionIA, VarianteProducto

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

# --- SISTEMA DE SINÓNIMOS Y MAPEO INTELIGENTE ---
CLOTHING_SYNONYMS = {
    "remera": ["camiseta", "playera", "polo", "shirt", "t-shirt", "tshirt"],
    "campera": ["chaqueta", "jacket", "abrigo", "chamarra", "cazadora"],
    "pantalon": ["jean", "jeans", "vaquero", "pants", "trouser", "leggins"],
    "buzo": ["sudadera", "hoodie", "pullover", "jersey"],
    "vestido": ["dress", "túnica", "robe"],
    "pollera": ["falda", "skirt"],
    "short": ["shorts", "bermuda", "pantalón corto"],
    "zapatillas": ["sneakers", "tenis", "deportivas", "zapatos"],
    "accesorios": ["accessories", "complementos", "extras"]
}

COLOR_SYNONYMS = {
    "negro": ["black", "oscuro"],
    "blanco": ["white", "claro"],
    "azul": ["blue", "marino", "celeste"],
    "rojo": ["red", "colorado", "bermejo"],
    "verde": ["green", "esmeralda"],
    "amarillo": ["yellow", "dorado"],
    "rosa": ["pink", "rosado"],
    "gris": ["gray", "grey", "plomo"],
    "marrón": ["brown", "café", "camel"],
    "violeta": ["purple", "morado"]
}

SIZE_SYNONYMS = {
    "xs": ["extra small", "muy chico"],
    "s": ["small", "chico", "pequeño"],
    "m": ["medium", "mediano", "medio"],
    "l": ["large", "grande"],
    "xl": ["extra large", "muy grande"],
    "xxl": ["doble extra large", "súper grande"]
}

INTENTION_KEYWORDS = {
    "product_search": ["busco", "quiero", "necesito", "me gusta", "mostrame", "tenes", "tienen", "ver", "mirar"],
    "size_inquiry": ["talle", "talles", "size", "sizes", "medida", "medidas"],
    "price_inquiry": ["precio", "precios", "cost", "cuesta", "vale", "barato", "caro"],
    "availability": ["stock", "hay", "disponible", "disponibilidad", "quedan"],
    "shipping": ["envio", "envíos", "shipping", "delivery", "entrega"],
    "help": ["ayuda", "help", "no se", "confundido", "información"],
    "greeting": ["hola", "hello", "hi", "buenas", "buenos días", "buenas tardes"]
}

async def analyze_user_intention(query: str) -> Dict[str, Any]:
    """Analiza la intención del usuario en base a palabras clave y patrones."""
    query_lower = query.lower()
    
    intentions = {}
    for intention, keywords in INTENTION_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in query_lower)
        if score > 0:
            intentions[intention] = score
    
    # Detectar patrones específicos
    patterns = {
        "specific_product": bool(re.search(r'\b(remera|campera|pantalon|buzo|vestido)\b', query_lower)),
        "color_mentioned": bool(re.search(r'\b(negro|blanco|azul|rojo|verde|amarillo|rosa|gris|marrón|violeta)\b', query_lower)),
        "size_mentioned": bool(re.search(r'\b(xs|s|m|l|xl|xxl|talle|size)\b', query_lower)),
        "price_range": bool(re.search(r'\$\d+|\d+\s*(peso|dollar|barato|caro)', query_lower))
    }
    
    # Determinar intención principal
    primary_intention = "general_inquiry"
    if intentions:
        primary_intention = max(intentions.keys(), key=lambda k: intentions[k])
    
    return {
        "primary_intention": primary_intention,
        "intentions": intentions,
        "patterns": patterns,
        "confidence": max(intentions.values()) if intentions else 0
    }

def normalize_search_terms(query: str) -> List[str]:
    """Normaliza términos de búsqueda incluyendo sinónimos."""
    query_lower = query.lower()
    terms = []
    
    # Buscar sinónimos de ropa
    for main_term, synonyms in CLOTHING_SYNONYMS.items():
        if main_term in query_lower or any(syn in query_lower for syn in synonyms):
            terms.append(main_term)
            terms.extend(synonyms)
    
    # Buscar sinónimos de colores
    for main_color, synonyms in COLOR_SYNONYMS.items():
        if main_color in query_lower or any(syn in query_lower for syn in synonyms):
            terms.append(main_color)
            terms.extend(synonyms)
    
    # Buscar sinónimos de talles
    for main_size, synonyms in SIZE_SYNONYMS.items():
        if main_size in query_lower or any(syn in query_lower for syn in synonyms):
            terms.append(main_size)
            terms.extend(synonyms)
    
    # Agregar palabras originales
    original_words = re.findall(r'\b\w+\b', query_lower)
    terms.extend(original_words)
    
    return list(set(terms))  # Eliminar duplicados

async def smart_product_search(db: AsyncSession, query: str, limit: int = 8) -> Dict[str, Any]:
    """Búsqueda inteligente de productos con análisis semántico."""
    try:
        intention_analysis = await analyze_user_intention(query)
        search_terms = normalize_search_terms(query)
        
        # Construir query base con variantes
        base_query = select(Producto).options(
            selectinload(Producto.categoria),
            selectinload(Producto.variantes)
        )
        
        # Condiciones de búsqueda
        conditions = []
        
        # Búsqueda por nombre y descripción
        name_conditions = []
        for term in search_terms:
            name_conditions.extend([
                Producto.nombre.ilike(f'%{term}%'),
                Producto.descripcion.ilike(f'%{term}%'),
                Producto.material.ilike(f'%{term}%'),
                Producto.color.ilike(f'%{term}%'),
                Producto.talle.ilike(f'%{term}%')
            ])
        
        if name_conditions:
            conditions.append(or_(*name_conditions))
        
        # Búsqueda por categoría
        if intention_analysis["patterns"]["specific_product"]:
            category_conditions = []
            for term in search_terms:
                category_conditions.append(
                    Producto.categoria.has(nombre=term.title())
                )
            if category_conditions:
                conditions.append(or_(*category_conditions))
        
        # Filtro por color específico si se mencionó
        if intention_analysis["patterns"]["color_mentioned"]:
            color_conditions = []
            for term in search_terms:
                if term in COLOR_SYNONYMS or any(term in synonyms for synonyms in COLOR_SYNONYMS.values()):
                    color_conditions.append(Producto.color.ilike(f'%{term}%'))
            if color_conditions:
                conditions.append(or_(*color_conditions))
        
        # Filtro por talle si se mencionó
        if intention_analysis["patterns"]["size_mentioned"]:
            size_conditions = []
            for term in search_terms:
                if term in SIZE_SYNONYMS or any(term in synonyms for synonyms in SIZE_SYNONYMS.values()):
                    size_conditions.extend([
                        Producto.talle.ilike(f'%{term}%'),
                        Producto.variantes.any(VarianteProducto.tamanio.ilike(f'%{term}%'))
                    ])
            if size_conditions:
                conditions.append(or_(*size_conditions))
        
        # Aplicar condiciones
        if conditions:
            final_query = base_query.where(or_(*conditions))
        else:
            # Si no hay condiciones específicas, buscar en todos los campos
            general_search = or_(
                *[Producto.nombre.ilike(f'%{term}%') for term in search_terms[:3]]  # Limitar a primeros 3 términos
            )
            final_query = base_query.where(general_search)
        
        # Ejecutar búsqueda
        result = await db.execute(final_query.limit(limit))
        products = result.scalars().unique().all()
        
        # Calcular score de relevancia
        scored_products = []
        for product in products:
            score = calculate_relevance_score(product, search_terms, intention_analysis)
            scored_products.append((product, score))
        
        # Ordenar por relevancia
        scored_products.sort(key=lambda x: x[1], reverse=True)
        
        return {
            "products": [p[0] for p in scored_products],
            "search_terms": search_terms,
            "intention_analysis": intention_analysis,
            "total_found": len(scored_products)
        }
        
    except Exception as e:
        logger.error(f"Error en búsqueda inteligente: {e}")
        return {
            "products": [],
            "search_terms": [],
            "intention_analysis": {},
            "total_found": 0
        }

def calculate_relevance_score(product: Producto, search_terms: List[str], intention_analysis: Dict) -> float:
    """Calcula score de relevancia para un producto."""
    score = 0.0
    
    # Puntos por coincidencias en nombre (peso alto)
    for term in search_terms:
        if term.lower() in product.nombre.lower():
            score += 10.0
    
    # Puntos por coincidencias en categoría
    if hasattr(product, 'categoria') and product.categoria:
        for term in search_terms:
            if term.lower() in product.categoria.nombre.lower():
                score += 8.0
    
    # Puntos por coincidencias en descripción
    if product.descripcion:
        for term in search_terms:
            if term.lower() in product.descripcion.lower():
                score += 5.0
    
    # Puntos por coincidencias en color
    if product.color:
        for term in search_terms:
            if term.lower() in product.color.lower():
                score += 7.0
    
    # Puntos por coincidencias en material
    if product.material:
        for term in search_terms:
            if term.lower() in product.material.lower():
                score += 6.0
    
    # Bonus por tener stock disponible
    if hasattr(product, 'variantes') and product.variantes:
        total_stock = sum(v.cantidad_en_stock for v in product.variantes)
        if total_stock > 0:
            score += 5.0
            if total_stock > 10:
                score += 3.0  # Bonus extra por buen stock
    
    # Bonus por intención específica
    if intention_analysis.get("primary_intention") == "product_search":
        score += 2.0
    
    return score
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
    """Define la personalidad y las instrucciones avanzadas del chatbot."""
    return (
        "Eres Kara, la asistente de ventas experta de VOID Indumentaria, una marca de ropa urbana y moderna. "
        "PERSONALIDAD: Eres súper cool, conocedora de moda, amigable y profesional. Hablás en argentino informal pero elegante. "
        "REGLAS IMPORTANTES:\n"
        "1. NUNCA digas que eres una IA o modelo de lenguaje - sos Kara, point.\n"
        "2. Usá la información del catálogo para responder sobre productos específicos\n"
        "3. Si no tenés info exacta, decilo clarito y ofrecé contactar a un humano\n"
        "4. Mantené respuestas concisas (máximo 60 palabras) pero útiles\n"
        "5. Cuando muestres productos, incluí ID, nombre, precio y si hay stock\n"
        "6. Si preguntan por talles, mostrarles los talles disponibles\n"
        "7. Para consultas de envíos: 'Los envíos se coordinan al finalizar la compra'\n"
        "8. Para pagos: 'Aceptamos MercadoPago con todas las opciones de pago'\n"
        "EJEMPLOS DE RESPUESTAS:\n"
        "- '¡Hola! Soy Kara 👋 ¿Qué tipo de ropa estás buscando hoy?'\n"
        "- 'Te muestro estas camperas que tenemos: [productos]'\n"
        "- 'Esa remera está disponible en talles M y L. ¿Cuál preferís?'\n"
        "- 'No tengo esa info exacta, pero puedo conectarte con el equipo para más detalles'"
    )

def get_enhanced_system_prompt(user_preferences: Dict = None, intention_analysis: Dict = None) -> str:
    """Genera un prompt del sistema personalizado según las preferencias del usuario."""
    base_prompt = get_chatbot_system_prompt()
    
    if user_preferences or intention_analysis:
        enhancements = []
        
        if user_preferences:
            if user_preferences.get("preferred_categories"):
                cats = ", ".join(user_preferences["preferred_categories"])
                enhancements.append(f"NOTA: Este usuario ha mostrado interés en: {cats}")
            
            if user_preferences.get("preferred_colors"):
                colors = ", ".join(user_preferences["preferred_colors"])
                enhancements.append(f"Colores que le interesan: {colors}")
            
            if user_preferences.get("preferred_sizes"):
                sizes = ", ".join(user_preferences["preferred_sizes"])
                enhancements.append(f"Talles que maneja: {sizes}")
        
        if intention_analysis:
            intent = intention_analysis.get("primary_intention", "")
            if intent == "product_search":
                enhancements.append("FOCO: El usuario está buscando productos específicos")
            elif intent == "size_inquiry":
                enhancements.append("FOCO: El usuario pregunta por talles disponibles")
            elif intent == "price_inquiry":
                enhancements.append("FOCO: El usuario está interesado en precios")
            elif intent == "availability":
                enhancements.append("FOCO: El usuario pregunta por disponibilidad/stock")
        
        if enhancements:
            base_prompt += "\n\nCONTEXTO PERSONALIZADO:\n" + "\n".join(enhancements)
    
    return base_prompt

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

# --- NUEVAS FUNCIONES MEJORADAS ---

async def get_enhanced_catalog_from_db(db: AsyncSession, user_query: str = None) -> str:
    """Obtiene el catálogo de productos formateado y optimizado según la consulta."""
    try:
        base_query = select(Producto).options(
            selectinload(Producto.categoria),
            selectinload(Producto.variantes)
        )
        
        # Si hay una consulta específica, usar búsqueda inteligente
        if user_query:
            search_result = await smart_product_search(db, user_query, limit=6)
            products = search_result["products"]
            
            if not products:
                # Fallback: obtener productos aleatorios si no hay matches
                result = await db.execute(base_query.limit(8))
                products = result.scalars().all()
        else:
            # Sin consulta específica, obtener todos los productos
            result = await db.execute(base_query)
            products = result.scalars().all()
        
        if not products:
            return "No hay productos disponibles en este momento."
        
        catalog_lines = ["--- CATÁLOGO VOID INDUMENTARIA ---"]
        
        for prod in products:
            category = prod.categoria.nombre if getattr(prod, 'categoria', None) else 'Sin categoría'
            color = prod.color or 'N/A'
            material = prod.material or 'N/A'
            descripcion = prod.descripcion or 'Sin descripción'
            
            # Información de variantes y stock
            stock_info = "Sin stock"
            available_sizes = []
            total_stock = 0
            
            if hasattr(prod, 'variantes') and prod.variantes:
                available_sizes = [v.tamanio for v in prod.variantes if v.cantidad_en_stock > 0]
                total_stock = sum(v.cantidad_en_stock for v in prod.variantes)
                
                if total_stock > 0:
                    stock_info = f"Stock: {total_stock} unidades"
                    if available_sizes:
                        stock_info += f" | Talles disponibles: {', '.join(set(available_sizes))}"
            
            # Construir línea del producto
            catalog_lines.append(
                f"🔹 ID: {prod.id} | {prod.nombre} | Categoría: {category} | "
                f"Color: {color} | Material: {material} | Precio: ${prod.precio} | "
                f"{stock_info} | Descripción: {descripcion}"
            )
        
        catalog_lines.append("--- FIN DEL CATÁLOGO ---")
        return "\n".join(catalog_lines)
        
    except Exception as e:
        logger.error(f"Error al obtener el catálogo mejorado: {e}")
        return "Error al obtener el catálogo."

async def get_personalized_recommendations(db: AsyncSession, session_id: str, limit: int = 4) -> List[Producto]:
    """Genera recomendaciones personalizadas basadas en el historial de conversaciones."""
    try:
        # Obtener historial de conversaciones del usuario
        result = await db.execute(
            select(ConversacionIA)
            .filter(ConversacionIA.sesion_id == session_id)
            .order_by(ConversacionIA.creado_en.desc())
            .limit(10)
        )
        conversations = result.scalars().all()
        
        # Analizar preferencias del historial
        preferences = analyze_user_preferences(conversations)
        
        # Construir query de recomendaciones
        query = select(Producto).options(
            selectinload(Producto.categoria),
            selectinload(Producto.variantes)
        )
        
        # Filtrar por preferencias detectadas
        conditions = []
        
        if preferences.get("preferred_categories"):
            category_conditions = []
            for cat in preferences["preferred_categories"]:
                category_conditions.append(Producto.categoria.has(nombre=cat))
            conditions.append(or_(*category_conditions))
        
        if preferences.get("preferred_colors"):
            color_conditions = []
            for color in preferences["preferred_colors"]:
                color_conditions.append(Producto.color.ilike(f'%{color}%'))
            conditions.append(or_(*color_conditions))
        
        if preferences.get("preferred_sizes"):
            size_conditions = []
            for size in preferences["preferred_sizes"]:
                size_conditions.append(Producto.variantes.any(VarianteProducto.tamanio.ilike(f'%{size}%')))
            conditions.append(or_(*size_conditions))
        
        # Aplicar filtros si existen preferencias
        if conditions:
            query = query.where(or_(*conditions))
        
        # Ordenar por popularidad y stock
        query = query.order_by(Producto.id.desc()).limit(limit * 2)  # Obtener más para filtrar
        
        result = await db.execute(query)
        products = result.scalars().all()
        
        # Filtrar productos con stock
        products_with_stock = [
            p for p in products 
            if hasattr(p, 'variantes') and p.variantes and 
            sum(v.cantidad_en_stock for v in p.variantes) > 0
        ]
        
        return products_with_stock[:limit]
        
    except Exception as e:
        logger.error(f"Error generando recomendaciones: {e}")
        return []

def analyze_user_preferences(conversations: List[ConversacionIA]) -> Dict[str, List[str]]:
    """Analiza las preferencias del usuario basado en sus conversaciones."""
    preferences = {
        "preferred_categories": [],
        "preferred_colors": [],
        "preferred_sizes": [],
        "interests": []
    }
    
    all_text = " ".join([conv.prompt.lower() for conv in conversations if conv.prompt])
    
    # Detectar categorías mencionadas
    for main_term, synonyms in CLOTHING_SYNONYMS.items():
        if main_term in all_text or any(syn in all_text for syn in synonyms):
            preferences["preferred_categories"].append(main_term.title())
    
    # Detectar colores mencionados
    for main_color, synonyms in COLOR_SYNONYMS.items():
        if main_color in all_text or any(syn in all_text for syn in synonyms):
            preferences["preferred_colors"].append(main_color)
    
    # Detectar talles mencionados
    for main_size, synonyms in SIZE_SYNONYMS.items():
        if main_size in all_text or any(syn in all_text for syn in synonyms):
            preferences["preferred_sizes"].append(main_size.upper())
    
    # Limpiar duplicados
    for key in preferences:
        preferences[key] = list(set(preferences[key]))
    
    return preferences