#!/bin/bash

# Script para iniciar el worker de Celery
exec celery -A celery_worker worker --queues=transactional --loglevel=info -n worker_tx
