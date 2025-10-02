# settings.py
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # =================================================================
    #  CONFIGURACIÓN DE LA APP Y ENTORNO
    # =================================================================
    APP_ENV: str = "development"

    FRONTEND_URL: str
    BACKEND_URL: str

    # =================================================================
    #  BASES DE DATOS
    # =================================================================
    DB_SQL_URI: str
    DB_NOSQL_URI: str

    # =================================================================
    #  SEGURIDAD Y JWT
    # =================================================================
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # =================================================================
    #  SERVICIOS DE TERCEROS
    # =================================================================
    # --- OpenRouter (opcional, solo si lo usás) ---
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_API_URL: str | None = None
    OPENROUTER_MODEL: str | None = None

    # --- Groq (el que ya tenés configurado) ---
    GROQ_API_KEY: str | None = None
    GROQ_MODEL_NAME: str | None = None

    # --- MercadoPago ---
    MERCADOPAGO_TOKEN: str

    # --- Cloudinary ---
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    # --- Email ---
    EMAIL_SENDER: str
    EMAIL_APP_PASSWORD: str

    # --- Nombre de la tienda ---
    SITE_NAME: str

    # --- Sentry ---
    SENTRY_DSN: str | None = None

    # --- Redis (opcional) ---
    REDIS_URL: str | None = None

    # =================================================================
    #  CONFIG
    # =================================================================
    @staticmethod
    def get_env_file():
        env = os.getenv("APP_ENV", "development")
        return f".env.{env}" if env != "development" else ".env"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra='ignore'
    )


# Instancia global
settings = Settings()

# --- AJUSTE DINÁMICO DE REDIS_URL ---
# Si no estamos en un contenedor Docker, y la URL de Redis apunta al hostname 'redis',
# la cambiamos a 'localhost'. Esto permite que la misma configuración .env
# funcione tanto para desarrollo local como para Docker.
import os
if not os.path.exists('/.dockerenv') and settings.REDIS_URL and '://redis:' in settings.REDIS_URL:
    print("INFO: Entorno local detectado. Cambiando Redis host a 'localhost'.")
    settings.REDIS_URL = settings.REDIS_URL.replace('://redis:', '://localhost:')
