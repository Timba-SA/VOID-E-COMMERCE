"""
Script de migración para agregar traducciones i18n a las categorías existentes.
Ejecutar una sola vez después de actualizar el modelo.
"""

import asyncio
from database.database import get_db_async
from database.models import Categoria
from sqlalchemy import select

# Mapeo de categorías existentes a sus traducciones
CATEGORY_TRANSLATIONS = {
    "Remeras": {"es": "Remeras", "en": "T-shirts"},
    "T-shirts": {"es": "Remeras", "en": "T-shirts"},
    "remeras": {"es": "Remeras", "en": "T-shirts"},
    "shirts": {"es": "Remeras", "en": "Shirts"},  # ⭐ AGREGADO
    "Shirts": {"es": "Remeras", "en": "Shirts"},  # ⭐ AGREGADO
    "Buzos": {"es": "Buzos", "en": "Hoodies"},
    "Hoodies": {"es": "Buzos", "en": "Hoodies"},
    "hoodies": {"es": "Buzos", "en": "Hoodies"},
    "Camperas": {"es": "Camperas", "en": "Jackets"},
    "Jackets": {"es": "Camperas", "en": "Jackets"},
    "jackets": {"es": "Camperas", "en": "Jackets"},
    "camperas": {"es": "Camperas", "en": "Jackets"},
    "Pantalones": {"es": "Pantalones", "en": "Pants"},
    "Pants": {"es": "Pantalones", "en": "Pants"},
    "pants": {"es": "Pantalones", "en": "Pants"},
    "pantalones": {"es": "Pantalones", "en": "Pants"},
    "Jeans": {"es": "Jeans", "en": "Jeans"},
    "Shorts": {"es": "Shorts", "en": "Shorts"},
    "shorts": {"es": "Shorts", "en": "Shorts"},
    "Vestidos": {"es": "Vestidos", "en": "Dresses"},
    "Dresses": {"es": "Vestidos", "en": "Dresses"},
    "vestidos": {"es": "Vestidos", "en": "Dresses"},
    "Polleras": {"es": "Polleras", "en": "Skirts"},
    "Skirts": {"es": "Polleras", "en": "Skirts"},
    "Bolsos": {"es": "Bolsos", "en": "Bags"},
    "Bags": {"es": "Bolsos", "en": "Bags"},
    "bolsos": {"es": "Bolsos", "en": "Bags"},
    "buzos": {"es": "Buzos", "en": "Bags"},  # ⭐ AGREGADO
    "Mochilas": {"es": "Mochilas", "en": "Backpacks"},
    "Backpacks": {"es": "Mochilas", "en": "Backpacks"},
    "Accesorios": {"es": "Accesorios", "en": "Accessories"},
    "Accessories": {"es": "Accesorios", "en": "Accessories"},
    "Tops": {"es": "Tops", "en": "Tops"},
    "tops": {"es": "Tops", "en": "Tops"},
}

async def migrate_categories():
    """Migra las categorías existentes para agregar traducciones i18n."""
    async for db in get_db_async():
        try:
            # Obtener todas las categorías
            result = await db.execute(select(Categoria))
            categories = result.scalars().all()
            
            print(f"Encontradas {len(categories)} categorías para migrar...")
            
            updated_count = 0
            for category in categories:
                # Si ya tiene nombre_i18n, saltear
                if category.nombre_i18n:
                    print(f"⏭️  '{category.nombre}' ya tiene traducciones, saltando...")
                    continue
                
                # Buscar traducción en el mapeo
                translation = CATEGORY_TRANSLATIONS.get(category.nombre)
                
                if translation:
                    category.nombre_i18n = translation
                    print(f"✅ Actualizando '{category.nombre}' con: {translation}")
                    updated_count += 1
                else:
                    # Si no hay traducción predefinida, crear una básica
                    default_translation = {
                        "es": category.nombre,
                        "en": category.nombre
                    }
                    category.nombre_i18n = default_translation
                    print(f"⚠️  No hay traducción para '{category.nombre}', usando valor por defecto: {default_translation}")
                    updated_count += 1
            
            # Guardar cambios
            await db.commit()
            print(f"\n🎉 Migración completada! {updated_count} categorías actualizadas.")
            
        except Exception as e:
            print(f"❌ Error durante la migración: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(migrate_categories())
