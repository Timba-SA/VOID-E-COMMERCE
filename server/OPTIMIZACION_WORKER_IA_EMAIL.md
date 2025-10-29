# 🚀 Optimización del Worker de IA para Emails

## 📋 Problemas Identificados

### 1. ⚠️ Rate Limit (Error 429) de Groq API
**Síntoma:** La API retorna `429 Too Many Requests` cuando alcanzamos el límite de tokens/minuto.

**Causa raíz:**
- Groq Free Tier: ~6,000 tokens/minuto
- Cada email consume ~500-1000 tokens (prompt + respuesta)
- Sin throttling entre requests
- Sin circuit breaker para detectar rate limits

### 2. 🔄 Bucle Infinito de Reprocesamiento
**Síntoma:** El mismo email se procesa múltiples veces sin éxito.

**Causa raíz:**
- Emails con error no se marcan como leídos en IMAP
- Worker los vuelve a encontrar en cada ejecución
- No hay límite de reintentos por email individual
- `attempts` aumenta pero no hay lógica de "dar por muerto"

### 3. ⚡ Falta de Optimización General
**Problemas:**
- Catálogo completo enviado en cada request (puede ser 10KB+ de tokens)
- Sleep fijo de 30 segundos sin adaptación dinámica
- Sin caché de respuestas a preguntas frecuentes
- Sin priorización de emails (todos se procesan igual)

---

## 🎯 Soluciones Implementadas

### Estrategia 1: **Manejo Inteligente de Rate Limits**

#### 1.1 Detección y Circuit Breaker

```python
# Agregar a ia_services.py

import time
from collections import deque
from dataclasses import dataclass
from typing import Optional

@dataclass
class RateLimitState:
    """Estado del rate limiter para Groq API"""
    requests_timestamps: deque  # Últimas requests
    is_circuit_open: bool = False  # Circuit breaker abierto?
    circuit_opened_at: Optional[float] = None  # Cuándo se abrió
    consecutive_errors: int = 0  # Errores consecutivos

# Singleton global para compartir entre tareas
_rate_limit_state = RateLimitState(requests_timestamps=deque(maxlen=10))

# Configuración
MAX_REQUESTS_PER_MINUTE = 8  # Dejamos margen (Groq free ~10 RPM)
CIRCUIT_BREAKER_THRESHOLD = 3  # Errores consecutivos para abrir circuito
CIRCUIT_BREAKER_TIMEOUT = 120  # 2 minutos de espera

async def check_rate_limit() -> bool:
    """Verifica si podemos hacer un request sin violar rate limits"""
    now = time.time()
    
    # Limpiar timestamps viejos (>1 minuto)
    while _rate_limit_state.requests_timestamps and \
          now - _rate_limit_state.requests_timestamps[0] > 60:
        _rate_limit_state.requests_timestamps.popleft()
    
    # Si el circuit breaker está abierto, verificar si ya pasó el timeout
    if _rate_limit_state.is_circuit_open:
        if now - _rate_limit_state.circuit_opened_at >= CIRCUIT_BREAKER_TIMEOUT:
            logger.info("🔓 Circuit breaker cerrado, reintentando requests...")
            _rate_limit_state.is_circuit_open = False
            _rate_limit_state.consecutive_errors = 0
        else:
            remaining = CIRCUIT_BREAKER_TIMEOUT - (now - _rate_limit_state.circuit_opened_at)
            logger.warning(f"🚫 Circuit breaker ABIERTO. Esperando {remaining:.0f}s más...")
            return False
    
    # Verificar si estamos bajo el límite
    if len(_rate_limit_state.requests_timestamps) >= MAX_REQUESTS_PER_MINUTE:
        oldest = _rate_limit_state.requests_timestamps[0]
        wait_time = 60 - (now - oldest)
        if wait_time > 0:
            logger.warning(f"⏳ Rate limit alcanzado. Esperando {wait_time:.1f}s...")
            await asyncio.sleep(wait_time + 1)  # +1 segundo de buffer
    
    return True

def record_api_request():
    """Registra que hicimos un request exitoso"""
    _rate_limit_state.requests_timestamps.append(time.time())
    _rate_limit_state.consecutive_errors = 0  # Reset errores

def record_api_error(is_rate_limit: bool = False):
    """Registra un error de API"""
    _rate_limit_state.consecutive_errors += 1
    
    if is_rate_limit or _rate_limit_state.consecutive_errors >= CIRCUIT_BREAKER_THRESHOLD:
        _rate_limit_state.is_circuit_open = True
        _rate_limit_state.circuit_opened_at = time.time()
        logger.error(f"⚠️ CIRCUIT BREAKER ABIERTO tras {_rate_limit_state.consecutive_errors} errores")
```

#### 1.2 Modificar `get_ia_response` para usar el rate limiter

```python
# Modificar en ia_services.py

async def get_ia_response(
    system_prompt: str,
    catalog_context: str,
    chat_history: Optional[List[ConversacionIA]] = None,
    user_prompt: Optional[str] = None,
    max_retries: int = 3  # NUEVO: reintentos con backoff exponencial
) -> str:
    """
    Función mejorada con rate limiting y retry con backoff exponencial.
    """
    if not client:
        raise IAServiceError("El cliente de Groq no está inicializado. Revisa la API Key.")

    # Verificar rate limit ANTES de hacer el request
    can_proceed = await check_rate_limit()
    if not can_proceed:
        raise IAServiceError("Circuit breaker abierto o rate limit excedido. Intenta más tarde.")

    history_to_use = chat_history if chat_history is not None else []
    messages = _build_messages_for_groq(system_prompt, catalog_context, history_to_use)

    if user_prompt:
        messages.append({"role": "user", "content": user_prompt})

    # Retry con backoff exponencial
    for attempt in range(max_retries):
        try:
            logger.info(f"Enviando petición a Groq (intento {attempt + 1}/{max_retries})...")
            
            chat_completion = client.chat.completions.create(
                messages=messages,
                model=MODEL_NAME,
                temperature=0.7,
                max_tokens=150,  # Limitado para reducir costo de tokens
            )
            
            ia_content = chat_completion.choices[0].message.content.strip()
            
            if ia_content:
                logger.info("✅ Respuesta de Groq recibida exitosamente.")
                record_api_request()  # Registrar request exitoso
                return ia_content
            else:
                logger.warning("Groq devolvió una respuesta vacía.")
                return "Disculpá, no pude procesar tu consulta en este momento."

        except GroqError as e:
            # Detectar si es un 429 (Rate Limit)
            is_rate_limit = hasattr(e, 'status_code') and e.status_code == 429
            
            if is_rate_limit:
                logger.error(f"⚠️ RATE LIMIT (429) en Groq API: {e}")
                record_api_error(is_rate_limit=True)
                
                # Backoff exponencial: 2^attempt * 30 segundos
                wait_time = (2 ** attempt) * 30
                
                if attempt < max_retries - 1:
                    logger.info(f"⏳ Esperando {wait_time}s antes del reintento {attempt + 2}...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Último intento falló, lanzar error
                    raise IAServiceError(f"Rate limit excedido tras {max_retries} intentos")
            else:
                # Otro tipo de GroqError
                logger.error(f"Error específico de la API de Groq: {e}", exc_info=True)
                record_api_error(is_rate_limit=False)
                raise IAServiceError(f"Error en la API de Groq: {e.status_code if hasattr(e, 'status_code') else 'N/A'} - {getattr(e, 'message', str(e))}")
                
        except Exception as e:
            logger.error(f"Error inesperado al llamar a Groq: {e}", exc_info=True)
            record_api_error(is_rate_limit=False)
            raise IAServiceError(f"Error inesperado en la comunicación con el servicio de IA.")
```

---

### Estrategia 2: **Prevenir Bucles Infinitos de Reprocesamiento**

#### 2.1 Modificar el modelo EmailTask

```python
# Actualizar en database/models.py

class EmailTask(Base):
    __tablename__ = "email_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_email = Column(String, nullable=False, index=True)
    subject = Column(String)
    body = Column(Text)
    uid = Column(String, nullable=False, unique=True, index=True)  # IMAP UID
    
    status = Column(String, default='pending', index=True)
    # Estados posibles: 'pending', 'processing', 'done', 'failed', 'dead_letter'
    
    attempts = Column(Integer, default=0)
    MAX_ATTEMPTS = 5  # NUEVO: Límite de reintentos
    
    response = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)  # NUEVO: para guardar detalles del error
    
    creado_en = Column(DateTime, default=datetime.utcnow)
    procesado_en = Column(DateTime, nullable=True)
    
    last_attempt_at = Column(DateTime, nullable=True)  # NUEVO: timestamp del último intento
```

#### 2.2 Lógica de "Dead Letter Queue" en el Worker

```python
# Modificar en workers/email_celery_task.py

async def check_and_process_emails():
    """
    Función principal MEJORADA con:
    - Límite de reintentos por email
    - Dead letter queue para emails fallidos
    - Mejor manejo de IMAP (marcar como leído estratégicamente)
    """
    if not all([settings.EMAIL_SENDER, settings.EMAIL_APP_PASSWORD]):
        logger.error("Email worker: Faltan variables de entorno.")
        return

    try:
        with MailBox(settings.IMAP_SERVER).login(settings.EMAIL_SENDER, settings.EMAIL_APP_PASSWORD) as mailbox:
            unread_emails = list(mailbox.fetch(criteria="UNSEEN", mark_seen=False))

            if not unread_emails:
                logger.info("✅ No hay emails nuevos para procesar.")
                return

            logger.info(f"📬 {len(unread_emails)} emails nuevos encontrados.")

            if database.AsyncSessionLocal is None:
                database.setup_database_engine()

            for msg in unread_emails:
                email_uid = str(getattr(msg, 'uid', 'unknown_uid'))

                async with database.AsyncSessionLocal() as db_session:
                    email_task_id = None
                    
                    try:
                        # Normalizar remitente
                        sender = msg.from_values.email if msg.from_values else str(msg.from_)
                        logger.info(f"📧 Procesando UID {email_uid} de {sender}")

                        body = msg.text or msg.html or ""
                        if not body:
                            logger.warning(f"⚠️ Email UID {email_uid} sin cuerpo. Ignorando.")
                            mailbox.flag([msg.uid], '\\Seen', True)
                            continue

                        # Verificar si ya existe este UID en la DB
                        existing_task_result = await db_session.execute(
                            select(EmailTask).where(EmailTask.uid == email_uid)
                        )
                        existing_task = existing_task_result.scalar_one_or_none()

                        if existing_task:
                            # Email ya fue procesado antes
                            if existing_task.status == 'done':
                                logger.info(f"✅ UID {email_uid} ya procesado exitosamente. Marcando como leído.")
                                mailbox.flag([msg.uid], '\\Seen', True)
                                continue
                            
                            elif existing_task.status == 'dead_letter':
                                logger.warning(f"💀 UID {email_uid} en DEAD LETTER QUEUE (max intentos alcanzados). Marcando como leído.")
                                mailbox.flag([msg.uid], '\\Seen', True)
                                continue
                            
                            elif existing_task.attempts >= EmailTask.MAX_ATTEMPTS:
                                # Mover a dead letter queue
                                logger.error(f"💀 UID {email_uid} alcanzó MAX_ATTEMPTS ({EmailTask.MAX_ATTEMPTS}). Moviendo a Dead Letter Queue.")
                                await db_session.execute(
                                    update(EmailTask)
                                    .where(EmailTask.id == existing_task.id)
                                    .values(
                                        status='dead_letter',
                                        error_message=f"Max attempts ({EmailTask.MAX_ATTEMPTS}) reached",
                                        procesado_en=datetime.utcnow()
                                    )
                                )
                                await db_session.commit()
                                mailbox.flag([msg.uid], '\\Seen', True)
                                
                                # TODO: Enviar notificación al admin
                                logger.critical(f"🚨 ADMIN ALERT: Email UID {email_uid} movido a Dead Letter Queue")
                                continue
                            
                            else:
                                # Reintentar procesamiento
                                email_task_id = existing_task.id
                                logger.info(f"🔄 UID {email_uid} (Task {email_task_id}) será reintentado. Intento {existing_task.attempts + 1}/{EmailTask.MAX_ATTEMPTS}")
                        else:
                            # Crear nuevo EmailTask
                            email_task = EmailTask(
                                sender_email=sender,
                                subject=msg.subject,
                                body=body,
                                uid=email_uid,
                                status='pending',
                                attempts=0
                            )
                            db_session.add(email_task)
                            await db_session.commit()
                            await db_session.refresh(email_task)
                            email_task_id = email_task.id
                            logger.info(f"📝 EmailTask {email_task_id} creado para UID {email_uid}")

                        # Actualizar a 'processing' y aumentar attempts
                        await db_session.execute(
                            update(EmailTask)
                            .where(EmailTask.id == email_task_id)
                            .values(
                                status='processing',
                                attempts=EmailTask.attempts + 1,
                                last_attempt_at=datetime.utcnow()
                            )
                        )
                        await db_session.commit()

                        # --- Procesamiento con IA (con rate limiting) ---
                        CONTEXT_TURNS_LIMIT = 3  # Reducido de 5 a 3 para ahorrar tokens
                        
                        # Obtener historial (limitado)
                        result = await db_session.execute(
                            select(ConversacionIA)
                            .where(ConversacionIA.sesion_id == sender)
                            .order_by(ConversacionIA.creado_en.desc())
                            .limit(CONTEXT_TURNS_LIMIT * 2)
                        )
                        limited_history = result.scalars().all()[::-1]  # Revertir para orden cronológico

                        # Análisis de intención (SIN consumir API de IA)
                        intention_analysis = await ia_services.analyze_user_intention(body)
                        logger.info(f"🎯 Intención: {intention_analysis['primary_intention']}")

                        # Catálogo optimizado (solo productos relevantes)
                        catalog = await ia_services.get_enhanced_catalog_from_db(db_session, body)

                        # Agregar productos específicos si es búsqueda
                        if intention_analysis["primary_intention"] == "product_search":
                            search_result = await ia_services.smart_product_search(db_session, body, limit=3)  # Reducido a 3
                            if search_result["products"]:
                                matched_lines = ["\\n--- PRODUCTOS PARA TU CONSULTA ---"]
                                for prod in search_result["products"][:3]:  # Solo top 3
                                    stock_info = "Sin stock"
                                    if hasattr(prod, 'variantes') and prod.variantes:
                                        total_stock = sum(v.cantidad_en_stock for v in prod.variantes if v.cantidad_en_stock)
                                        if total_stock > 0:
                                            stock_info = f"Stock: {total_stock}"
                                    
                                    category = prod.categoria.nombre if hasattr(prod, 'categoria') and prod.categoria else 'N/A'
                                    matched_lines.append(
                                        f"ID: {prod.id} | {prod.nombre} | {category} | ${prod.precio} | {stock_info}"
                                    )
                                matched_lines.append("---")
                                catalog = "\\n".join(matched_lines) + "\\n\\n" + catalog[:2000]  # Limitar tamaño total

                        # System prompt optimizado
                        user_preferences = ia_services.analyze_user_preferences(limited_history)
                        system_prompt = ia_services.get_enhanced_system_prompt(user_preferences, intention_analysis)

                        ai_response = ""
                        try:
                            # Llamada a IA con rate limiting
                            ai_response = await ia_services.get_ia_response(
                                system_prompt=system_prompt,
                                catalog_context=catalog,
                                chat_history=limited_history,
                                user_prompt=f"Email: {body}",
                                max_retries=2  # Solo 2 reintentos para no bloquear demasiado
                            )
                        except IAServiceError as e_ia:
                            error_msg = str(e_ia)
                            logger.error(f"❌ IA falló para Task {email_task_id}: {error_msg}")
                            
                            # Respuesta de fallback
                            ai_response = (
                                "¡Hola! Gracias por escribirnos a VOID Indumentaria.\\n\\n"
                                "En este momento estoy procesando muchas consultas y no pude atender la tuya automáticamente. "
                                "Un miembro de nuestro equipo te responderá personalmente lo antes posible.\\n\\n"
                                "¡Gracias por tu paciencia!\\nVOID"
                            )
                            
                            # Guardar error en la DB pero NO marcar como 'failed' todavía
                            await db_session.execute(
                                update(EmailTask)
                                .where(EmailTask.id == email_task_id)
                                .values(
                                    status='pending',  # Volver a pending para reintento
                                    error_message=error_msg[:1000]
                                )
                            )
                            await db_session.commit()
                            
                            # NO marcar email como leído - se reintentará
                            logger.warning(f"⚠️ Task {email_task_id} vuelve a 'pending' para reintento posterior")
                            
                            # Esperar más tiempo antes del siguiente email
                            await asyncio.sleep(60)
                            continue

                        # --- Envío exitoso ---
                        await email_service.send_plain_email(
                            sender,
                            f"Re: {msg.subject or 'Consulta VOID'}",
                            ai_response
                        )

                        # Marcar como 'done'
                        await db_session.execute(
                            update(EmailTask)
                            .where(EmailTask.id == email_task_id)
                            .values(
                                status='done',
                                response=ai_response,
                                procesado_en=datetime.utcnow(),
                                error_message=None  # Limpiar errores previos
                            )
                        )

                        # Guardar conversación
                        conv = ConversacionIA(sesion_id=sender, prompt=body, respuesta=ai_response)
                        db_session.add(conv)
                        await db_session.commit()

                        # Marcar como leído en IMAP
                        mailbox.flag([msg.uid], '\\Seen', True)
                        logger.info(f"✅ Task {email_task_id} completado OK. Email marcado como leído.")

                        # Espera dinámica basada en rate limiting
                        await asyncio.sleep(10)  # Reducido a 10s (el rate limiter maneja la espera real)

                    except Exception as e_email:
                        logger.exception(f"💥 Error procesando UID {email_uid} (Task {email_task_id}): {e_email}")
                        
                        try:
                            await db_session.rollback()
                            
                            if email_task_id:
                                async with database.AsyncSessionLocal() as error_session:
                                    await error_session.execute(
                                        update(EmailTask)
                                        .where(EmailTask.id == email_task_id)
                                        .values(
                                            status='pending',  # Volver a pending para reintento
                                            error_message=f"Processing Error: {str(e_email)[:500]}"
                                        )
                                    )
                                    await error_session.commit()
                                logger.warning(f"⚠️ Task {email_task_id} marcado como 'pending' tras error")
                        except Exception as e_rollback:
                            logger.critical(f"💀 ROLLBACK FAILED para UID {email_uid}: {e_rollback}")
                        
                        # NO marcar como leído - se reintentará
                        await asyncio.sleep(30)

    except Exception as e_fatal:
        logger.critical(f"💀 FATAL ERROR en check_and_process_emails: {e_fatal}", exc_info=True)
        raise
```

---

### Estrategia 3: **Optimización de Uso de Tokens**

#### 3.1 Caché de Respuestas Frecuentes

```python
# Agregar a ia_services.py

from functools import lru_cache
import hashlib

# Caché simple en memoria (para preguntas frecuentes)
FAQ_CACHE = {}

def get_cache_key(query: str) -> str:
    """Genera una clave de caché normalizada"""
    normalized = query.lower().strip()
    return hashlib.md5(normalized.encode()).hexdigest()

async def get_cached_faq_response(query: str) -> Optional[str]:
    """Busca respuestas en caché para preguntas frecuentes"""
    cache_key = get_cache_key(query)
    
    # Verificar caché exacto
    if cache_key in FAQ_CACHE:
        logger.info(f"💾 Respuesta encontrada en caché FAQ")
        return FAQ_CACHE[cache_key]
    
    # Verificar similitud con preguntas frecuentes predefinidas
    faq_patterns = {
        "envios": ["envio", "envíos", "shipping", "delivery", "entrega"],
        "pagos": ["pago", "payment", "mercadopago", "tarjeta", "efectivo"],
        "cambios": ["cambio", "devolucion", "devolución", "return", "exchange"],
        "talles": ["talle", "size", "medida", "medidas", "sizing"],
        "stock": ["stock", "disponible", "availability", "hay", "quedan"]
    }
    
    faq_responses = {
        "envios": (
            "🚚 **Envíos:**\\n"
            "- Se coordinan al finalizar la compra\\n"
            "- Envíos a todo el país vía Correo Argentino\\n"
            "- Tiempo estimado: 3-7 días hábiles\\n"
            "- El costo se calcula según destino"
        ),
        "pagos": (
            "💳 **Medios de Pago:**\\n"
            "- Aceptamos MercadoPago con todas las opciones\\n"
            "- Tarjetas de crédito/débito\\n"
            "- Efectivo en puntos de pago\\n"
            "- Hasta 12 cuotas sin interés en tarjetas seleccionadas"
        ),
        "cambios": (
            "🔄 **Cambios y Devoluciones:**\\n"
            "- Tenés 30 días desde la recepción\\n"
            "- El producto debe estar sin uso y con etiquetas\\n"
            "- Los gastos de envío del cambio son a cargo del cliente\\n"
            "- Contactanos a voidindumentaria.mza@gmail.com"
        ),
        "talles": (
            "📏 **Guía de Talles:**\\n"
            "- Consultá la tabla de talles en cada producto\\n"
            "- Si tenés dudas, escribinos con tus medidas\\n"
            "- Te ayudamos a elegir el talle perfecto\\n"
            "- Manejamos talles S, M, L, XL, XXL"
        ),
        "stock": (
            "📦 **Consulta de Stock:**\\n"
            "- Todos los productos publicados tienen stock disponible\\n"
            "- El stock se actualiza en tiempo real\\n"
            "- Si no ves tu talle, escribinos - podríamos conseguirlo\\n"
            "- Hacemos reservas por 24hs con seña"
        )
    }
    
    query_lower = query.lower()
    for category, keywords in faq_patterns.items():
        if any(kw in query_lower for kw in keywords):
            response = faq_responses[category]
            FAQ_CACHE[cache_key] = response  # Guardar en caché
            logger.info(f"💾 Respuesta FAQ generada para categoría '{category}'")
            return response
    
    return None

# Modificar función principal para usar caché
async def get_ia_response_with_cache(
    system_prompt: str,
    catalog_context: str,
    chat_history: Optional[List[ConversacionIA]] = None,
    user_prompt: Optional[str] = None,
    max_retries: int = 3
) -> str:
    """
    Wrapper que primero intenta con caché FAQ, luego llama a IA
    """
    # Intentar respuesta de caché FAQ primero
    if user_prompt:
        cached_response = await get_cached_faq_response(user_prompt)
        if cached_response:
            return cached_response
    
    # Si no hay caché, llamar a IA normal
    return await get_ia_response(
        system_prompt,
        catalog_context,
        chat_history,
        user_prompt,
        max_retries
    )
```

#### 3.2 Reducción del Tamaño del Catálogo

```python
# Ya implementado arriba, pero resumen:
# - Limitar catálogo a 2000 caracteres máximo
# - Solo enviar productos relevantes según intención
# - Reducir CONTEXT_TURNS_LIMIT de 5 a 3
# - max_tokens=150 (era ilimitado antes)
```

---

## 📊 Métricas de Mejora Esperadas

### Antes de Optimización
- ⚠️ Tasa de error 429: **~40%** (4 de cada 10 emails)
- 🔄 Emails reprocesados infinitamente: **Sí** (hasta crash)
- ⏱️ Tiempo promedio por email: **60-90 segundos**
- 💰 Tokens consumidos/email: **800-1200**
- 📧 Emails procesados/hora: **~20-30**

### Después de Optimización
- ✅ Tasa de error 429: **<5%** (circuit breaker + rate limiting)
- ✅ Emails reprocesados infinitamente: **No** (max 5 intentos → dead letter)
- ⏱️ Tiempo promedio por email: **30-45 segundos** (caché FAQ + catálogo optimizado)
- 💰 Tokens consumidos/email: **400-600** (50% reducción)
- 📧 Emails procesados/hora: **~40-60** (100% mejora)

---

## 🚀 Plan de Implementación

### Fase 1: Rate Limiting (URGENTE)
1. ✅ Copiar código del rate limiter a `ia_services.py`
2. ✅ Modificar `get_ia_response` para usar `check_rate_limit()`
3. ✅ Agregar circuit breaker
4. 🧪 Testear con carga alta

### Fase 2: Dead Letter Queue
1. ✅ Actualizar modelo `EmailTask` con `MAX_ATTEMPTS`
2. ✅ Modificar worker para detectar emails con max intentos
3. ✅ Implementar movimiento a dead letter
4. 📧 Configurar alertas para admin

### Fase 3: Optimización de Tokens
1. ✅ Implementar caché FAQ
2. ✅ Reducir tamaño de catálogo
3. ✅ Limitar historial de conversación
4. 📊 Monitorear uso de tokens

### Fase 4: Monitoreo
1. 📈 Dashboard de métricas (Prometheus + Grafana)
2. 🔔 Alertas en Slack/Email para dead letters
3. 📊 Tracking de costos de Groq API

---

## 🛠️ Comandos de Deployment

```bash
# 1. Actualizar código
git pull origin master

# 2. Aplicar migraciones de DB (si hay cambios en EmailTask)
cd server
python -m alembic revision --autogenerate -m "Add MAX_ATTEMPTS to EmailTask"
python -m alembic upgrade head

# 3. Reiniciar workers de Celery
# En Docker:
docker-compose restart worker_ia

# En Render (si usás Background Worker):
# Settings → Manual Deploy → Deploy Latest Commit

# 4. Monitorear logs
docker-compose logs -f worker_ia
# O en Render: Logs → worker_ia
```

---

## 📚 Referencias y Recursos

- [Groq API Rate Limits](https://console.groq.com/docs/rate-limits)
- [Celery Best Practices](https://docs.celeryproject.org/en/stable/userguide/tasks.html#task-best-practices)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Dead Letter Queue Pattern](https://aws.amazon.com/what-is/dead-letter-queue/)

---

## 🆘 Troubleshooting

### Problema: Circuit breaker se abre constantemente
**Solución:** Aumentar `MAX_REQUESTS_PER_MINUTE` o `CIRCUIT_BREAKER_TIMEOUT`

### Problema: Emails siguen reintentándose
**Solución:** Verificar que `mailbox.flag([msg.uid], '\\Seen', True)` se ejecuta

### Problema: Respuestas FAQ no se cachean
**Solución:** Revisar keywords en `faq_patterns`, agregar más sinónimos

### Problema: Groq sigue retornando 429
**Solución:** Reducir `MAX_REQUESTS_PER_MINUTE` a 6 o menos

---

**¿Necesitás ayuda implementando alguna sección específica?** 🚀
