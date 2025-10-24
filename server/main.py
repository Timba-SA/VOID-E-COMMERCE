# En BACKEND/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import database # <--- ¡IMPORTANTE!
import sentry_sdk
from settings import settings
from database.models import Base, Categoria
from routers import (
    health_router, auth_router, products_router, cart_router,
    admin_router, chatbot_router, checkout_router, orders_router,
    user_router, categories_router, utils_router, wishlist_router,
    ai_search_router
)
from utils.limiter import limiter, RateLimitExceeded, _rate_limit_exceeded_handler

# --- ACÁ ESTÁ LA MAGIA CORREGIDA ---
async def seed_initial_data():
    """Función para cargar datos iniciales si no existen."""
    async with database.AsyncSessionLocal() as db:
        result = await db.execute(select(Categoria))
        if result.scalars().first() is None:
            print("Base de datos de categorías vacía. Cargando datos iniciales...")
            
            # --- ¡LA LISTA BUENA, LA QUE VOS QUERÉS! ---
            DEFAULT_CATEGORIES = [
                "Hoodies",
                "Jackets",
                "Shirts",
                "Pants",
                "Dresses",
                "Tops",
                "Accessories"
            ]
            # -----------------------------------------

            for cat_name in DEFAULT_CATEGORIES:
                db.add(Categoria(nombre=cat_name))
            await db.commit()
            print("Categorías iniciales cargadas con éxito.")
        else:
            print("La base de datos de categorías ya tiene datos.")

# --- Configuración de Sentry ---
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        traces_sample_rate=1.0,
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- ACÁ EMPIEZAN LOS CAMBIOS ---
    print("DEBUG: Iniciando lifespan...") # <-- AGREGADO
    
    database.setup_database_engine()
    print(f"DEBUG: Engine SQL configurado. Intentando conectar a URL: {database.SQLALCHEMY_DATABASE_URL}") # <-- AGREGADO (Usa la variable de tu módulo database)

    # --- Prueba de Conexión SQL (La que está fallando) ---
    try:
        print(f"DEBUG: Probando conexión inicial a SQL...") # <-- AGREGADO
        # Esta es la línea crítica donde falla según tus logs
        async with database.engine.begin() as conn:
            print("✅ Conexión inicial a SQL exitosa. Intentando crear tablas (run_sync)...") # <-- AGREGADO
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Tablas SQL verificadas/creadas (run_sync).") # <-- AGREGADO
    except Exception as e:
        # Este print te dirá el error exacto si falla la conexión o create_all
        print(f"🔥 Error en conexión SQL inicial o create_all (lifespan): {e}") # <-- AGREGADO (o asegurate de que esté)

    print("DEBUG: Intentando ejecutar seed_initial_data()...") # <-- AGREGADO
    try:
        await seed_initial_data()
        print("✅ seed_initial_data() ejecutado.") # <-- AGREGADO
    except Exception as e:
        print(f"🔥 Error durante seed_initial_data(): {e}") # <-- AGREGADO

    # --- La app corre ---
    yield

    # --- Limpieza al cerrar ---
    print("DEBUG: Cerrando lifespan...") # <-- AGREGADO
    if hasattr(app.state, 'mongo_client'): # Si usaste Mongo
        app.state.mongo_client.close()
        print("🔌 Conexión con MongoDB cerrada.")

    # El dispose del engine SQL
    if database.engine: # Chequea si existe el engine antes de cerrar
        print("DEBUG: Intentando cerrar conexiones SQL (engine.dispose)...") # <-- AGREGADO
        await database.engine.dispose()
        print("🔌 Conexión SQL (engine) cerrada.") # <-- AGREGADO

app = FastAPI(
    title="VOID Backend - Optimizado",
    description="Backend ultra-rápido con cache agresivo, compresión y queries optimizadas.",
    version="0.7.0",
    lifespan=lifespan
)

# Agregar compresión GZIP para respuestas más rápidas
# Comprime respuestas > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = [
    "https://void-frontend-g0hf.onrender.com", # El dominio de tu frontend en producción
    "http://localhost:5173",                 # El dominio de tu frontend para desarrollo local
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"mensaje": "Backend de VOID funcionando (Sprint 6)."}

# Incluimos todos los routers
app.include_router(health_router.router)
app.include_router(auth_router.router)
app.include_router(products_router.router)
app.include_router(cart_router.router)
app.include_router(admin_router.router)
app.include_router(chatbot_router.router)
app.include_router(checkout_router.router)
app.include_router(orders_router.router)
app.include_router(user_router.router)
app.include_router(categories_router.router)
app.include_router(utils_router.router)
app.include_router(wishlist_router.router)
app.include_router(ai_search_router.router)