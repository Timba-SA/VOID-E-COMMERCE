import redis.asyncio as redis
import redis as redis_sync
import json
from settings import settings

# Pool async para operaciones asíncronas
redis_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)

# Cliente síncrono para operaciones no-async (usado por routers con Response)
try:
    redis_client = redis_sync.from_url(settings.REDIS_URL, decode_responses=True)
except:
    redis_client = None

# ============ FUNCIONES SÍNCRONAS (Nuevas) ============

def get_cache(key: str):
    """Obtiene un valor del caché de Redis (versión síncrona)."""
    try:
        if not redis_client:
            return None
        cached_data = redis_client.get(key)
        if cached_data:
            return cached_data  # Ya viene como string
        return None
    except Exception as e:
        print(f"ERROR AL OBTENER DEL CACHÉ: {e}")
        return None

def set_cache(key: str, value: str, ttl: int = 3600):
    """Guarda un valor en el caché (versión síncrona)."""
    try:
        if not redis_client:
            return
        redis_client.setex(key, ttl, value)
    except Exception as e:
        print(f"ERROR AL GUARDAR EN EL CACHÉ: {e}")

def delete_cache(key: str):
    """Elimina una key del cache (versión síncrona)."""
    try:
        if not redis_client:
            return
        redis_client.delete(key)
    except Exception as e:
        print(f"ERROR AL ELIMINAR DEL CACHÉ: {e}")

def delete_pattern(pattern: str):
    """Elimina todas las keys que coincidan con el patrón (versión síncrona)."""
    try:
        if not redis_client:
            return
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
    except Exception as e:
        print(f"ERROR AL ELIMINAR PATRÓN DEL CACHÉ: {e}")

# ============ FUNCIONES ASÍNCRONAS (Originales) ============

async def get_cache_async(key: str):
    """Obtiene un valor del caché de Redis (versión async)."""
    try:
        r = redis.Redis(connection_pool=redis_pool)
        cached_data = await r.get(key)
        if cached_data:
            return json.loads(cached_data)
        return None
    except Exception as e:
        print(f"ERROR AL OBTENER DEL CACHÉ: {e}")
        return None

async def set_cache_async(key: str, value: any, expire_seconds: int = 3600):
    """Guarda un valor en el caché de Redis (versión async)."""
    try:
        r = redis.Redis(connection_pool=redis_pool)
        await r.set(key, json.dumps(value), ex=expire_seconds)
    except Exception as e:
        print(f"ERROR AL GUARDAR EN EL CACHÉ: {e}")