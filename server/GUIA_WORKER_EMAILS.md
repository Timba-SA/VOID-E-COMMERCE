# 📧 Guía: Cómo Levantar el Worker de Emails

## 📋 Tabla de Contenidos

1. [Requisitos Previos](#-requisitos-previos)
2. [Configuración](#-configuración)
3. [Levantar el Worker Localmente](#-levantar-el-worker-localmente)
4. [Levantar el Worker en Docker](#-levantar-el-worker-en-docker)
5. [Levantar el Worker en Producción (Render)](#-levantar-el-worker-en-producción-render)
6. [Monitoreo y Logs](#-monitoreo-y-logs)
7. [Troubleshooting](#-troubleshooting)

---

## 🔧 Requisitos Previos

### Software Necesario

- **Python 3.11+**
- **Redis** (para Celery)
- **PostgreSQL** (base de datos)
- **Docker** y **Docker Compose** (opcional, para desarrollo)

### Variables de Entorno Requeridas

Asegurate de tener configuradas estas variables en tu archivo `.env`:

```env
# Email Configuration
EMAIL_SENDER=tu-email@gmail.com
EMAIL_APP_PASSWORD=tu-contraseña-de-app-de-16-digitos
IMAP_SERVER=imap.gmail.com

# Groq API
GROQ_API_KEY=gsk_xxxxxxxxxxxxx
GROQ_MODEL_NAME=llama-3.3-70b-versatile

# Redis (para Celery)
REDIS_URL=redis://localhost:6379/0

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname
```

### Habilitar Gmail para IMAP

1. Ve a tu cuenta de Google → **Seguridad**
2. Activa **Verificación en 2 pasos**
3. Crea una **Contraseña de aplicación**:
   - Ve a: https://myaccount.google.com/apppasswords
   - Selecciona "Correo" y "Otro (Nombre personalizado)"
   - Copia la contraseña de 16 dígitos
   - Úsala en `EMAIL_APP_PASSWORD`
4. Habilita **IMAP** en Gmail:
   - Configuración → Ver todos los ajustes → Reenvío y correo POP/IMAP
   - Marca "Habilitar IMAP"

---

## ⚙️ Configuración

### 1. Instalar Dependencias

```bash
cd server
pip install -r requirements.txt
```

### 2. Verificar que Redis esté corriendo

**En Windows (con Chocolatey):**
```powershell
choco install redis-64
redis-server
```

**En Linux/Mac:**
```bash
redis-server
```

**Verificar conexión:**
```bash
redis-cli ping
# Debe responder: PONG
```

### 3. Aplicar Migraciones de Base de Datos

Si agregaste los nuevos campos a `EmailTask`:

```bash
cd server
python -m alembic revision --autogenerate -m "Add MAX_ATTEMPTS to EmailTask"
python -m alembic upgrade head
```

---

## 💻 Levantar el Worker Localmente

### Opción 1: Worker de IA (emails automatizados)

```bash
cd server

# Levantar el worker de IA en cola worker_ia
celery -A celery_worker worker --loglevel=info --pool=solo -Q worker_ia
```

### Opción 2: Worker Transaccional (emails de confirmación, etc.)

```bash
cd server

# Levantar el worker transaccional en cola worker_tx
celery -A celery_worker worker --loglevel=info --pool=solo -Q worker_tx
```

### Opción 3: Ambos Workers Simultáneamente

**Terminal 1 - Worker IA:**
```bash
celery -A celery_worker worker --loglevel=info --pool=solo -Q worker_ia -n worker_ia@%h
```

**Terminal 2 - Worker Transaccional:**
```bash
celery -A celery_worker worker --loglevel=info --pool=solo -Q worker_tx -n worker_tx@%h
```

### Opción 4: Worker con Beat (programar tareas periódicas)

```bash
# Iniciar Beat en una terminal separada
celery -A celery_worker beat --loglevel=info

# En otra terminal, iniciar el worker
celery -A celery_worker worker --loglevel=info --pool=solo -Q worker_ia
```

---

## 🐳 Levantar el Worker en Docker

### 1. Verificar `docker-compose.yml`

Asegurate de que tu `docker-compose.yml` incluya el servicio del worker:

```yaml
services:
  # ... otros servicios ...

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - void-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  worker_ia:
    build:
      context: ./server
      dockerfile: Dockerfile
    command: celery -A celery_worker worker --loglevel=info --pool=solo -Q worker_ia -n worker_ia@%h
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
      - EMAIL_SENDER=${EMAIL_SENDER}
      - EMAIL_APP_PASSWORD=${EMAIL_APP_PASSWORD}
      - GROQ_API_KEY=${GROQ_API_KEY}
      - GROQ_MODEL_NAME=${GROQ_MODEL_NAME}
      - IMAP_SERVER=imap.gmail.com
    depends_on:
      redis:
        condition: service_healthy
      db:
        condition: service_healthy
    networks:
      - void-network
    restart: unless-stopped

  worker_tx:
    build:
      context: ./server
      dockerfile: Dockerfile
    command: celery -A celery_worker worker --loglevel=info --pool=solo -Q worker_tx -n worker_tx@%h
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
      - EMAIL_SENDER=${EMAIL_SENDER}
      - EMAIL_APP_PASSWORD=${EMAIL_APP_PASSWORD}
    depends_on:
      redis:
        condition: service_healthy
      db:
        condition: service_healthy
    networks:
      - void-network
    restart: unless-stopped

  celery_beat:
    build:
      context: ./server
      dockerfile: Dockerfile
    command: celery -A celery_worker beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - void-network
    restart: unless-stopped

networks:
  void-network:
    driver: bridge
```

### 2. Levantar Todos los Servicios

```bash
docker-compose up --build
```

### 3. Ver Logs del Worker IA

```bash
docker-compose logs -f worker_ia
```

### 4. Reiniciar Solo el Worker IA

```bash
docker-compose restart worker_ia
```

---

## 🚀 Levantar el Worker en Producción (Render)

### Opción 1: Background Worker (Recomendado)

1. **Crear un nuevo Background Worker en Render:**
   - Dashboard → New → Background Worker
   - **Name:** `void-worker-ia`
   - **Environment:** Python 3
   - **Build Command:**
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     celery -A celery_worker worker --loglevel=info --pool=solo -Q worker_ia -n worker_ia@%h
     ```

2. **Variables de Entorno:**
   - Copia TODAS las variables del `.env` al panel de Render
   - Asegurate de que `REDIS_URL` apunte a tu instancia de Redis en Render

3. **Agregar Redis (si no lo tenés):**
   - Dashboard → New → Redis
   - Copia la URL generada y úsala en `REDIS_URL`

4. **Deploy:**
   - Render detectará cambios en tu repo y re-deployará automáticamente

### Opción 2: Celery Beat (para tareas programadas)

Si necesitás ejecutar tareas periódicas (ej: revisar emails cada 5 minutos):

1. **Crear otro Background Worker:**
   - **Name:** `void-celery-beat`
   - **Start Command:**
     ```bash
     celery -A celery_worker beat --loglevel=info
     ```

2. **Configurar Schedule en `celery_worker.py`:**

```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'check-emails-every-5-minutes': {
        'task': 'tasks.process_unread_emails',
        'schedule': crontab(minute='*/5'),  # Cada 5 minutos
    },
}
```

---

## 📊 Monitoreo y Logs

### Ver Logs en Tiempo Real

**Localmente:**
```bash
# Worker IA
celery -A celery_worker worker --loglevel=debug -Q worker_ia

# Flower (interfaz web para Celery)
pip install flower
celery -A celery_worker flower --port=5555
# Abrí http://localhost:5555 en tu navegador
```

**Docker:**
```bash
docker-compose logs -f worker_ia
```

**Render:**
- Dashboard → worker_ia → Logs

### Interpretando los Logs con Emojis

Los logs ahora usan emojis para identificar el tipo de operación:

- 🔌 **Conexión IMAP** - Conectándose al servidor de emails
- 📬 **Emails encontrados** - Cantidad de emails nuevos
- 📧 **Procesando email** - Email en proceso
- 👤 **Remitente** - Info del remitente
- 📝 **EmailTask creado** - Nuevo registro en DB
- 🔄 **Procesando** - Estado cambiado a processing
- 📚 **Historial** - Obteniendo conversaciones previas
- 🎯 **Intención** - Análisis de la consulta del usuario
- 📦 **Catálogo** - Generando lista de productos
- 🔍 **Búsqueda** - Búsqueda inteligente de productos
- 🤖 **IA** - Llamada a Groq API
- 💾 **Caché** - Respuesta desde FAQ caché
- ✅ **Éxito** - Operación completada
- ⏳ **Esperando** - Sleep entre emails
- ⚠️ **Advertencia** - Algo inusual pero no crítico
- ❌ **Error** - Operación fallida
- 💀 **Dead Letter** - Email enviado a cola de errores
- 🚨 **Alerta Admin** - Notificación crítica
- 💥 **Excepción** - Error grande capturado

### Ejemplo de Log Exitoso

```
2025-10-29 15:30:45 - [INFO] 📧 email_celery_task - 🔌 Conectando a servidor IMAP...
2025-10-29 15:30:46 - [INFO] 📧 email_celery_task - 📬 3 emails nuevos encontrados.
2025-10-29 15:30:46 - [INFO] 📧 email_celery_task - 📧 [1/3] Procesando UID 12345...
2025-10-29 15:30:46 - [INFO] 📧 email_celery_task - 👤 Remitente: cliente@example.com | Asunto: 'Consulta sobre remeras'
2025-10-29 15:30:46 - [INFO] 📧 email_celery_task - 📝 EmailTask 789 creado para UID 12345
2025-10-29 15:30:46 - [INFO] 📧 email_celery_task - 🔄 Task 789 marcado como 'processing'
2025-10-29 15:30:47 - [INFO] 📧 email_celery_task - 🎯 Intención detectada: product_search
2025-10-29 15:30:47 - [INFO] 📧 email_celery_task - 📦 Generando catálogo optimizado...
2025-10-29 15:30:47 - [INFO] 📧 email_celery_task - 🔍 Búsqueda de productos específicos...
2025-10-29 15:30:47 - [INFO] 📧 email_celery_task - ✅ 3 productos encontrados
2025-10-29 15:30:48 - [INFO] 📧 ia_services - 🤖 Enviando petición a Groq (intento 1/2)...
2025-10-29 15:30:50 - [INFO] 📧 ia_services - ✅ Respuesta de Groq recibida exitosamente.
2025-10-29 15:30:51 - [INFO] 📧 email_celery_task - 📤 Enviando email de respuesta a cliente@example.com...
2025-10-29 15:30:52 - [INFO] 📧 email_celery_task - ✅ Task 789 completado OK. Email marcado como leído.
2025-10-29 15:30:52 - [INFO] 📧 email_celery_task - ⏳ Esperando 10s antes del siguiente email...
```

---

## 🔍 Troubleshooting

### Problema: "Circuit breaker ABIERTO"

**Síntoma:**
```
🚫 Circuit breaker ABIERTO. Esperando 120s más...
```

**Causa:** Demasiados errores consecutivos de Groq API (3 o más).

**Solución:**
1. Esperar 2 minutos (se cierra automáticamente)
2. Verificar que `GROQ_API_KEY` sea válida
3. Revisar límites de tu plan de Groq
4. Reducir `MAX_REQUESTS_PER_MINUTE` en `ia_services.py` (línea 47)

### Problema: "Rate limit alcanzado"

**Síntoma:**
```
⏳ Rate limit alcanzado. Esperando 45.3s...
```

**Causa:** Alcanzaste el límite de 8 requests/minuto.

**Solución:**
- Es normal, el sistema esperará automáticamente
- Si ocurre muy seguido, reducir `MAX_REQUESTS_PER_MINUTE` a 6

### Problema: Emails en Dead Letter Queue

**Síntoma:**
```
💀 UID 12345 alcanzó MAX_ATTEMPTS (5). Moviendo a Dead Letter Queue.
🚨 ADMIN ALERT: Email UID 12345 movido a Dead Letter Queue
```

**Causa:** Email falló 5 veces consecutivas.

**Solución:**
1. Revisar logs para ver el error original
2. Consultar `email_tasks` en la DB:
   ```sql
   SELECT * FROM email_tasks WHERE status = 'dead_letter' ORDER BY creado_en DESC;
   ```
3. Ver campo `error_message` para detalles
4. Reprocesar manualmente:
   ```python
   from workers.email_celery_task_OPTIMIZED import reprocess_email_task
   reprocess_email_task.apply_async(args=[email_task_id])
   ```

### Problema: "AsyncSessionLocal no está inicializado"

**Síntoma:**
```
❌ AsyncSessionLocal no está inicializado en el proceso worker.
```

**Solución:**
```bash
# Reiniciar el worker
docker-compose restart worker_ia

# O localmente
# Ctrl+C para detener, luego:
celery -A celery_worker worker --loglevel=info --pool=solo -Q worker_ia
```

### Problema: Redis Connection Error

**Síntoma:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solución:**
1. Verificar que Redis esté corriendo:
   ```bash
   redis-cli ping
   ```
2. Verificar `REDIS_URL` en `.env`:
   ```env
   # Localmente
   REDIS_URL=redis://localhost:6379/0
   
   # Docker
   REDIS_URL=redis://redis:6379/0
   
   # Render
   REDIS_URL=redis://red-xxxxx.render.com:6379
   ```

### Problema: IMAP Login Failed

**Síntoma:**
```
imaplib.IMAP4.error: [AUTHENTICATIONFAILED] Invalid credentials
```

**Solución:**
1. Verificar que `EMAIL_APP_PASSWORD` sea la contraseña de app (16 dígitos)
2. Verificar que IMAP esté habilitado en Gmail
3. Regenerar contraseña de app si es necesario

### Problema: Worker se detiene sin logs

**Causa:** Timeout de Celery (configurado en 300 segundos).

**Solución:**
Aumentar `time_limit` en la tarea:

```python
@celery_app.task(
    name='tasks.process_unread_emails',
    time_limit=600  # 10 minutos en vez de 5
)
```

---

## 📈 Mejoras Implementadas

### ✅ Nuevas Funcionalidades

1. **Dead Letter Queue**
   - Emails con 5 intentos fallidos → estado `dead_letter`
   - No se reintenta automáticamente
   - Genera alerta para admin

2. **Circuit Breaker**
   - Se abre tras 3 errores consecutivos de Groq
   - Espera 2 minutos antes de reintentar
   - Previene colapso por rate limits

3. **Rate Limiting**
   - Máximo 8 requests/minuto a Groq API
   - Espera automática si se alcanza el límite
   - Previene error 429

4. **Caché FAQ**
   - Respuestas instantáneas para preguntas frecuentes
   - No consume API de Groq
   - 5 categorías: envíos, pagos, cambios, talles, stock

5. **Logs Mejorados**
   - Emojis para identificar tipo de operación
   - Timestamps claros
   - Nivel de detalle ajustable

6. **Optimización de Tokens**
   - Historial reducido: 3 turnos (vs 5 anterior)
   - Catálogo limitado a 2000 chars
   - max_tokens=150 en Groq
   - **50% reducción de tokens consumidos**

7. **Backoff Exponencial**
   - Primer reintento: 30s de espera
   - Segundo reintento: 60s de espera
   - Tercer reintento: 120s de espera

---

## 🎯 Próximos Pasos

1. **Monitoreo en Producción:**
   - Configurar alertas en Render para Dead Letter emails
   - Implementar dashboard con métricas de Flower

2. **Optimizaciones Adicionales:**
   - Implementar caché Redis para catálogo completo
   - Agregar batch processing (procesar múltiples emails en paralelo)
   - Tracking de costos de Groq API

3. **Testing:**
   - Tests unitarios para `get_ia_response_with_cache`
   - Tests de integración para Dead Letter Queue
   - Simular rate limits para validar circuit breaker

---

## 📞 Soporte

Si tenés problemas:

1. Revisá los logs con `docker-compose logs -f worker_ia`
2. Verificá el estado de Redis con `redis-cli ping`
3. Consultá la tabla `email_tasks` para ver errores:
   ```sql
   SELECT id, sender_email, status, attempts, error_message 
   FROM email_tasks 
   WHERE status IN ('failed', 'dead_letter') 
   ORDER BY creado_en DESC 
   LIMIT 10;
   ```

---

**¡Listo! 🎉** Tu worker de emails está optimizado y listo para producción.
