from celery import Celery
from celery.signals import worker_process_init
import os
from dotenv import load_dotenv

# --- Importamos nuestra función de setup de la base de datos ---
from database.database import setup_database_engine

# Cargamos las variables de entorno desde el archivo .env
load_dotenv()

# --- Hook para la señal de Celery: Se ejecuta al iniciar un proceso worker ---
@worker_process_init.connect
def init_worker(**kwargs):
    """
    Esta función se ejecuta CADA VEZ que un proceso worker de Celery arranca.
    Es el lugar perfecto para inicializar conexiones de DB por proceso.
    """
    # Usamos os.getpid() para ver el ID del proceso y confirmar que se crea uno nuevo cada vez
    print(f"🚀 Proceso worker (PID: {os.getpid()}) iniciado. Configurando la conexión a la DB...")
    setup_database_engine()

# --- Configuración principal de la App de Celery ---
celery_app = Celery(
    # El nombre de la app, comúnmente 'tasks'
    "tasks",
    # URL del broker (Redis) para la comunicación entre procesos
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    # URL del backend (Redis) para almacenar los resultados de las tareas
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
    # Lista de módulos donde Celery debe buscar tareas (@celery_app.task)
    include=[
        'workers.email_celery_task',
        'workers.transactional_tasks'
    ]
)

# --- Configuración del Planificador (Beat) para tareas periódicas ---
celery_app.conf.beat_schedule = {
    'check-emails-every-minute': {
        # El nombre COMPLETO de la tarea que queremos ejecutar.
        # Debe coincidir con el 'name' en el decorador @celery_app.task
        'task': 'tasks.process_unread_emails',
        # La frecuencia en segundos
        'schedule': 60.0,
    },
    # Podrías agregar más tareas programadas aquí
    # 'cleanup-old-data': {
    #     'task': 'workers.maintenance_tasks.cleanup',
    #     'schedule': 3600.0, # cada hora
    # },
}

# --- Configuración de la zona horaria ---
# Es importante para que el planificador (Beat) sepa cuándo ejecutar las tareas.
celery_app.conf.timezone = 'America/Argentina/Buenos_Aires'