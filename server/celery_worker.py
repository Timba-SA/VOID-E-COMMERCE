# /server/celery_worker.py

from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

celery_app = Celery(
    "tasks",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
    
    # --- ASEGURATE DE QUE ESTA PARTE QUEDE EXACTAMENTE ASÍ ---
    # Es una lista de Python con dos strings, separados por una coma.
    include=[
        'workers.email_celery_task',
        'workers.transactional_tasks'
    ] 
)

# El resto del archivo
celery_app.conf.beat_schedule = {
    'check-emails-every-minute': {
        'task': 'tasks.process_unread_emails',
        'schedule': 60.0,
    },
}

celery_app.conf.timezone = 'America/Argentina/Buenos_Aires'