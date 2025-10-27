"""
Script simple para agregar traducciones i18n a la categoría 'shirts'
"""
import asyncio
import sys
import os

# Agregar el directorio server al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from database.models import Categoria

# Leer URL de la base de datos desde las variables de entorno
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ Error: No se encontró la variable DATABASE_URL")
    print("   Por favor, asegúrate de que el archivo .env existe y contiene DATABASE_URL")
    sys.exit(1)

print(f"🔗 Usando base de datos: {DATABASE_URL[:30]}...")

# Mapeo de traducciones
CATEGORY_TRANSLATIONS = {
    "shirts": {"es": "Remeras", "en": "Shirts"},
    "Shirts": {"es": "Remeras", "en": "Shirts"},
    "hoodies": {"es": "Buzos", "en": "Hoodies"},
    "Hoodies": {"es": "Buzos", "en": "Hoodies"},
    "jackets": {"es": "Camperas", "en": "Jackets"},
    "Jackets": {"es": "Camperas", "en": "Jackets"},
    "pants": {"es": "Pantalones", "en": "Pants"},
    "Pants": {"es": "Pantalones", "en": "Pants"},
    "shorts": {"es": "Shorts", "en": "Shorts"},
    "Shorts": {"es": "Shorts", "en": "Shorts"},
    "vestidos": {"es": "Vestidos", "en": "Dresses"},
    "Vestidos": {"es": "Vestidos", "en": "Dresses"},
    "bolsos": {"es": "Bolsos", "en": "Bags"},
    "Bolsos": {"es": "Bolsos", "en": "Bags"},
    "buzos": {"es": "Buzos", "en": "Hoodies"},
    "Buzos": {"es": "Buzos", "en": "Hoodies"},
    "camperas": {"es": "Camperas", "en": "Jackets"},
    "Camperas": {"es": "Camperas", "en": "Jackets"},
    "pantalones": {"es": "Pantalones", "en": "Pants"},
    "Pantalones": {"es": "Pantalones", "en": "Pants"},
    "tops": {"es": "Tops", "en": "Tops"},
    "Tops": {"es": "Tops", "en": "Tops"},
}

async def fix_translations():
    """Actualiza las traducciones de las categorías"""
    
    # Crear engine y session
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Obtener todas las categorías
            result = await session.execute(select(Categoria))
            categories = result.scalars().all()
            
            print(f"\n{'='*60}")
            print(f"Encontradas {len(categories)} categorías")
            print(f"{'='*60}\n")
            
            updated_count = 0
            
            for category in categories:
                print(f"📋 Categoría: '{category.nombre}'")
                print(f"   Traducción actual: {category.nombre_i18n}")
                
                # Buscar traducción
                translation = CATEGORY_TRANSLATIONS.get(category.nombre)
                
                if translation:
                    category.nombre_i18n = translation
                    print(f"   ✅ Actualizada a: {translation}")
                    updated_count += 1
                else:
                    # Si no hay traducción, crear una básica
                    if not category.nombre_i18n:
                        default_translation = {
                            "es": category.nombre,
                            "en": category.nombre
                        }
                        category.nombre_i18n = default_translation
                        print(f"   ⚠️  Creada traducción por defecto: {default_translation}")
                        updated_count += 1
                    else:
                        print(f"   ⏭️  Ya tiene traducción, saltando...")
                
                print()
            
            # Guardar cambios
            await session.commit()
            
            print(f"\n{'='*60}")
            print(f"🎉 ¡Migración completada!")
            print(f"   {updated_count} categorías actualizadas.")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    print("\n🚀 Iniciando migración de traducciones de categorías...")
    asyncio.run(fix_translations())
