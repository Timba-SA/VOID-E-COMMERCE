# 🔧 SOLUCIÓN: WORKER DE CELERY EN RENDER (Plan Gratuito)

## Problema Actual
El backend está intentando encolar emails pero NO hay ningún worker corriendo que los procese.

**Error en logs:**
```
📧 Encolando email de confirmación para orden 60
ERROR:celery.backends.redis:Connection to Redis lost
CRITICAL WORKER TIMEOUT
```

---

## SOLUCIÓN: Ejecutar Worker en el mismo proceso del Backend

Ya que el Background Worker es pago, vamos a ejecutar el worker de Celery **dentro del mismo servicio del backend**.

### Paso 1: Crear script de inicio

Creá un archivo llamado `start.sh` en la carpeta `server/`:

```bash
#!/bin/bash

# Iniciar Celery worker en background
celery -A celery_worker worker --queues=transactional --loglevel=info -n worker_tx &

# Iniciar Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT
```

### Paso 2: Dar permisos de ejecución (LOCAL)

En tu máquina local, antes de hacer commit:

```bash
cd server
chmod +x start.sh
git add start.sh
git commit -m "Add startup script with Celery worker"
git push
```

### Paso 3: Cambiar Start Command en Render

1. Ve a tu servicio **Backend** en Render
2. Settings → **Start Command**
3. Cambiá de:
   ```
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT
   ```
   A:
   ```
   bash start.sh
   ```

4. Click en **"Save Changes"**
5. Render va a re-deployar automáticamente

---

## ✅ Verificar que Funciona

Una vez que el backend esté Live nuevamente:

1. **Mirá los logs del Backend** - Deberías ver al inicio:
   ```
   [2025-xx-xx] celery@worker_tx ready.
   ```

2. **Hacé una compra de prueba**

3. **Revisá los logs del Backend** - Deberías ver:
   - `📧 Encolando email de confirmación para orden XX`
   - `✅ Email encolado exitosamente`
   - `🚀 TAREA DE EMAIL INICIADA - Orden ID: XX`
   - `✅ Email de confirmacion enviado exitosamente`

4. **Revisá tu email** - debería llegar la confirmación

---

## 🔍 Troubleshooting

### Si no arranca el backend:
- Verificá que el archivo `start.sh` tenga permisos de ejecución (`chmod +x`)
- Mirá los logs de deploy en Render para ver el error

### Si el worker no procesa emails:
- Verificá que `REDIS_URL` esté configurado en las variables de entorno
- Verificá que `EMAIL_SENDER` y `EMAIL_APP_PASSWORD` estén configurados
- Buscá errores tipo "Connection refused" en los logs

### Si el worker crashea:
- Puede ser falta de memoria. En ese caso, reducí los workers de Gunicorn:
  ```bash
  gunicorn -w 2 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT
  ```

---

## 📊 Resultado Final

Vas a tener **3 servicios en Render:**
1. ✅ **Backend** (Web Service) - API FastAPI + Worker Celery integrado
2. ✅ **Frontend** (Static Site o Web Service) - React
3. ✅ **Redis** (Key-Value Store) - Cola de tareas
