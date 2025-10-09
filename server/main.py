# En BACKEND/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    user_router, categories_router, utils_router, wishlist_router
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
    database.setup_database_engine()  # <--- LLAMADA CRÍTICA
    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await seed_initial_data()
    
    yield
    await database.engine.dispose()
# --- FIN DE LA MAGIA ---

app = FastAPI(
    title="VOID Backend - Finalizado",
    description="Backend con autenticación, catálogo de productos, carrito de compras, panel de admin y chatbot.",
    version="0.6.0",
    lifespan=lifespan
)

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