# En settings.py
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # =================================================================
    #  CONFIGURACIÓN DE LA APP Y ENTORNO
    # =================================================================
    # Esta variable nos dirá si estamos en 'development' o 'production'
    APP_ENV: str = "development"
    
    # URLs de la aplicación (¡chau hardcodeo!)
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
    # --- OpenRouter (para el Chatbot IA) ---
    OPENROUTER_API_KEY: str
    OPENROUTER_API_URL: str
    OPENROUTER_MODEL: str
    

    # --- MercadoPago ---
    MERCADOPAGO_TOKEN: str

    # --- Cloudinary (para imágenes) ---
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    # --- Email (con Gmail) ---
    EMAIL_SENDER: str
    EMAIL_APP_PASSWORD: str

    # --- Nombre de la tienda ---
    SITE_NAME: str

    # --- Sentry ---
    SENTRY_DSN: str | None = None  # Por defecto es None, ya que en desarrollo no lo usamos

    # --- Redis ---
    REDIS_URL: str

    # Esto le dice a Pydantic que lea las variables de un archivo .env
    @staticmethod
    def get_env_file():
        # Leemos la variable de entorno del sistema. Si no existe, usamos 'development'.
        env = os.getenv("APP_ENV", "development")
        return f".env.{env}" if env != "development" else ".env"

    model_config = SettingsConfigDict(
        env_file=get_env_file.__func__(), # Llamamos a nuestra función para obtener el nombre del archivo
        env_file_encoding='utf-8'
    )

# Creamos una única instancia que vamos a importar en todo el proyecto
settings = Settings()