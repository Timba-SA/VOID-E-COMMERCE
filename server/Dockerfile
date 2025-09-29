# Usamos una imagen oficial de Python, versión "slim" que es más liviana.
FROM python:3.11-slim

# Seteamos el directorio de trabajo DENTRO del contenedor.
WORKDIR /app

# Variable de entorno para que Python no guarde logs en buffer y los veamos al toque.
ENV PYTHONUNBUFFERED 1

# Copiamos solo los archivos de requerimientos primero.
# Esto es un truco de cache de Docker para que las instalaciones sean más rápidas.
COPY ./requirements.txt /app/requirements.txt
COPY ./requirements-dev.txt /app/requirements-dev.txt

# Instalamos TODAS las dependencias (incluidas las de desarrollo por ahora).
RUN pip install --no-cache-dir --upgrade -r /app/requirements-dev.txt

# Ahora sí, copiamos todo el resto de tu código del backend.
COPY . /app

# Exponemos el puerto 8000 del contenedor para que se pueda conectar desde afuera.
EXPOSE 8000

# El comando que se va a ejecutar cuando arranque el contenedor.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]