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
    print("DEBUG: Iniciando lifespan...")

    # --- Configuración y Prueba de Conexión SQL (Supabase) ---
    try:
        # Llama a la función que configura el engine (esta imprimirá la URL desde database.py)
        database.setup_database_engine()
        print(f"DEBUG: Engine SQL configurado. Probando conexión inicial...")

        # Intenta la conexión y la creación de tablas (o verificación)
        async with database.engine.begin() as conn:
            print("✅ Conexión inicial a SQL exitosa. Intentando run_sync(Base.metadata.create_all)...")
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Tablas SQL verificadas/creadas (run_sync).")

    except Exception as e:
        # Si falla la configuración, la conexión o create_all, imprimirá el error aquí
        print(f"🔥 Error CRÍTICO en conexión SQL inicial o setup/create_all (lifespan): {e}")
    print("DEBUG: Intentando ejecutar seed_initial_data()...")
    try:
        await seed_initial_data()
        print("✅ seed_initial_data() ejecutado (o ya existían datos).")
    except Exception as e:
        # Captura errores específicos del seeding si los hubiera
        print(f"🔥 Error durante seed_initial_data(): {e}")


    # --- La aplicación se ejecuta ---
    yield


    # --- Limpieza al cerrar la aplicación ---
    print("DEBUG: Cerrando lifespan...")
    if hasattr(app.state, 'mongo_client'): # Si inicializaste Mongo
        app.state.mongo_client.close()
        print("🔌 Conexión con MongoDB cerrada.")

    if database.engine: # Si el engine SQL se inicializó
        print("DEBUG: Intentando cerrar conexiones SQL (engine.dispose)...")
        await database.engine.dispose() # Cierra las conexiones del pool
        print("🔌 Conexiones SQL (engine) cerradas.")

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
    # --- Dominios de Render (Staging/Viejos) ---
    "https://void-frontend-g0hf.onrender.com",  # El front de Render
    "https://void-e-commerce-1.onrender.com", # El back de Render

    # --- Desarrollo Local ---
    "http://localhost:5173",  # React/Vite en tu compu
    "http://localhost:8000"   # El backend local
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