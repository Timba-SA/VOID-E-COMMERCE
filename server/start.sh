#!/bin/bash

# Iniciar Celery worker en background
celery -A celery_worker worker --queues=transactional --loglevel=info -n worker_tx &

# Iniciar Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT
