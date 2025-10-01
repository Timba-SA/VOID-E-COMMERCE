from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from settings import settings

# Creamos una instancia del limitador.
# La función 'get_remote_address' le dice al limitador que agrupe
# las peticiones por la dirección IP del que las hace.
# 'storage_uri' le dice que use nuestro Redis para guardar la cuenta.
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL
)