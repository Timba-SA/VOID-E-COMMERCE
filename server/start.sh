#!/bin/bash

# Función para iniciar Celery después de que Gunicorn esté listo
start_celery_delayed() {
    sleep 10
    celery -A celery_worker worker --queues=transactional --loglevel=info -n worker_tx
}

# Iniciar Celery en background (con delay)
start_celery_delayed &

# Iniciar Gunicorn INMEDIATAMENTE
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT
