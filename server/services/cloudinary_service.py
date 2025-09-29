# En BACKEND/services/cloudinary_service.py

import os
import cloudinary
import cloudinary.uploader
import re # Importamos el módulo de expresiones regulares
from settings import settings
from fastapi import HTTPException, UploadFile, status
from typing import List

# --- Configuración de Cloudinary ---
cloudinary.config(
    cloud_name = settings.CLOUDINARY_CLOUD_NAME,
    api_key = settings.CLOUDINARY_API_KEY,
    api_secret = settings.CLOUDINARY_API_SECRET,
    secure=True
)

# --- Constante para la carpeta de Cloudinary ---
CLOUDINARY_FOLDER = "void_ecommerce_products"

async def upload_images(files: List[UploadFile]) -> List[str]:
    """
    Sube una lista de archivos a Cloudinary y devuelve sus URLs seguras.
    """
    uploaded_urls = []
    for file in files:
        try:
            upload_result = cloudinary.uploader.upload(
                file.file,
                folder=CLOUDINARY_FOLDER,
                resource_type="image"
            )
            uploaded_urls.append(upload_result.get("secure_url"))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al subir la imagen '{file.filename}': {e}"
            )
    return uploaded_urls

# --- ¡NUEVA FUNCIÓN PARA BORRAR IMÁGENES! ---
async def delete_images(urls: List[str]):
    """
    Elimina una lista de imágenes de Cloudinary a partir de sus URLs.
    """
    for url in urls:
        try:
            # Extraemos el public_id de la URL. Es más robusto que hacer un simple split.
            # Buscamos la parte de la ruta que está dentro de nuestra carpeta de cloudinary.
            match = re.search(f"{CLOUDINARY_FOLDER}/(.*?)", url)
            if not match:
                print(f"No se pudo extraer el public_id de la URL: {url}")
                continue

            public_id_with_extension = match.group(1)
            public_id = os.path.splitext(public_id_with_extension)[0]
            full_public_id = f"{CLOUDINARY_FOLDER}/{public_id}"

            # Llamamos a la API de Cloudinary para destruir la imagen
            cloudinary.uploader.destroy(full_public_id, resource_type="image")
            
        except Exception as e:
            # Si algo falla, simplemente lo registramos en la consola y continuamos
            # para no detener el proceso de actualización por un error de borrado.
            print(f"Error al eliminar la imagen {url} de Cloudinary: {e}")