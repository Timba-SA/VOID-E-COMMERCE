# En BACKEND/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# --- IMPORTACIONES NUEVAS ---
from database.database import engine, AsyncSessionLocal
from database.models import Base, Categoria
# --- FIN IMPORTACIONES NUEVAS ---

from routers import (
    health_router, auth_router, products_router, cart_router,
    admin_router, chatbot_router, checkout_router, orders_router,
    user_router, categories_router
)

# --- ACÁ ESTÁ LA MAGIA CORREGIDA ---
async def seed_initial_data():
    """Función para cargar datos iniciales si no existen."""
    async with AsyncSessionLocal() as db:
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await seed_initial_data()
    
    yield
    await engine.dispose()
# --- FIN DE LA MAGIA ---

app = FastAPI(
    title="VOID Backend - Finalizado",
    description="Backend con autenticación, catálogo de productos, carrito de compras, panel de admin y chatbot.",
    version="0.6.0",
    lifespan=lifespan
)

origins = [
    "http://localhost",
    "http://localhost:5173",
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