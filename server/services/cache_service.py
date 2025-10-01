import redis.asyncio as redis
import json
from settings import settings

# Creamos una única "pileta" de conexiones para que la app la reutilice y sea más eficiente.
redis_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)

async def get_cache(key: str):
    """Obtiene un valor del caché de Redis."""
    try:
        r = redis.Redis(connection_pool=redis_pool)
        cached_data = await r.get(key)
        if cached_data:
            # Redis guarda texto, así que convertimos el texto JSON de vuelta a un objeto Python
            return json.loads(cached_data)
        return None
    except Exception as e:
        # Si Redis se cae, no queremos que toda la app explote.
        # Simplemente imprimimos el error y devolvemos None.
        print(f"ERROR AL OBTENER DEL CACHÉ: {e}")
        return None

async def set_cache(key: str, value: any, expire_seconds: int = 3600):
    """Guarda un valor en el caché de Redis con un tiempo de expiración (por defecto, 1 hora)."""
    try:
        r = redis.Redis(connection_pool=redis_pool)
        # Convertimos el objeto Python a un texto en formato JSON para poder guardarlo
        await r.set(key, json.dumps(value), ex=expire_seconds)
    except Exception as e:
        print(f"ERROR AL GUARDAR EN EL CACHÉ: {e}")