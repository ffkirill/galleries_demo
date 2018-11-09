from .settings import *

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'memcached:11211',
    }
}

SA_DATABASE_URL = 'postgresql://postgres:postgres@postgres:5432/postgres'
