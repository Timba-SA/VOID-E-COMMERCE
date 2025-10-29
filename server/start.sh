#!/bin/bash

# Solo iniciar Gunicorn - Celery se iniciará por separado
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT main:app
