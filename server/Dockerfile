# =================================================================
#  ETAPA 1: El "Taller" o "Builder"
#  Acá preparamos todo lo pesado.
# =================================================================
FROM python:3.11-slim AS builder

# Variable de entorno para que Python no guarde logs en buffer.
ENV PYTHONUNBUFFERED=1

# Seteamos el directorio de trabajo DENTRO del contenedor.
WORKDIR /app

# Primero, instalamos las dependencias de una forma optimizada.
# En lugar de 'pip install', creamos "wheels" (paquetes pre-compilados).
COPY ./requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt


# =================================================================
#  ETAPA 2: La Imagen Final (limpia y optimizada)
#  Acá solo ponemos lo estrictamente necesario.
# =================================================================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Copiamos las dependencias pre-compiladas de la etapa 'builder'.
COPY --from=builder /app/wheels /app/wheels

# Instalamos las dependencias desde los 'wheels' locales.
# Esto es mucho más rápido y no necesita conexión a internet.
RUN pip install --no-cache-dir /app/wheels/*

# Ahora sí, copiamos todo el código de nuestra aplicación.
COPY . /app

# Exponemos el puerto 8000 para que el mundo exterior pueda conectarse.
EXPOSE 8000

# =================================================================
#  EL COMANDO DE PRODUCCIÓN (¡La Magia!)
#  Reemplazamos 'uvicorn --reload' por Gunicorn.
# =================================================================
# Gunicorn es un 'manager' que maneja múltiples procesos de Uvicorn.
# -w 4: Inicia 4 "workers" (como 4 empleados atendiendo pedidos a la vez).
# -k uvicorn.workers.UvicornWorker: Le dice a Gunicorn que use la velocidad de Uvicorn.
# -b 0.0.0.0:${PORT:-8000}: Escucha en el puerto dinámico (Render usa $PORT, local usa 8000).
# main:app: Nuestro archivo 'main.py' y el objeto 'app' de FastAPI.
CMD gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT:-8000} main:app