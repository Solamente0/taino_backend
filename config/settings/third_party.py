from datetime import timedelta

import mongoengine

from .base import env
from .jazzmin_config import JAZZMIN_SETTINGS

UNAUTHENTICATED_USER = None
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASS": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "UNAUTHENTICATED_USER": None,
    "UNAUTHENTICATED_TOKEN": None,
}

REDIS_USERNAME = env.str("REDIS_CONNECTION_USERNAME")
REDIS_PASSWORD = env.str("REDIS_CONNECTION_PASSWORD")
REDIS_HOST = env.str("REDIS_CONNECTION_HOST", default="localhost")
REDIS_PORT = env.str("REDIS_CONNECTION_PORT", default="6379")

RABBITMQ_USERNAME = env.str("RABBITMQ_CONNECTION_USERNAME")
RABBITMQ_PASSWORD = env.str("RABBITMQ_CONNECTION_PASSWORD")
RABBITMQ_HOST = env.str("RABBITMQ_CONNECTION_HOST", default="localhost")
RABBITMQ_PORT = env.str("RABBITMQ_CONNECTION_PORT", default="5672")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

JWT_SIGNING_KEY = env.str("JWT_SIGNING_KEY", default="W^W[7Ij_!<Zk*J*R%X`iN^|x#,m1s596")
ACCESS_TOKEN_LIFETIME_MINUTES = env.int("ACCESS_TOKEN_LIFETIME_MINUTES", default=4320)
REFRESH_TOKEN_LIFETIME_MINUTES = env.int("REFRESH_TOKEN_LIFETIME_MINUTES", default=7200)
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=ACCESS_TOKEN_LIFETIME_MINUTES),
    "REFRESH_TOKEN_LIFETIME": timedelta(minutes=REFRESH_TOKEN_LIFETIME_MINUTES),
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": JWT_SIGNING_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "pid",
    "USER_ID_CLAIM": "user_pid",
    "JTI_CLAIM": "jti",
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

MONGODB_DBNAME = env.str("MONGODB_DBNAME", default="tainodb")
MONGODB_CONNECTION_USERNAME = env.str("MONGODB_CONNECTION_USERNAME", default="tainomongouser")
MONGODB_CONNECTION_PASSWORD = env.str("MONGODB_CONNECTION_PASSWORD", default="tainomongopass")
MONGODB_CONNECTION_HOST = env.str("MONGODB_CONNECTION_HOST", default="mongo")
MONGODB_CONNECTION_PORT = env.int("MONGODB_CONNECTION_PORT", default=27017)
MONGODB_AUTHSRC = env.str("MONGODB_AUTHSRC", default="admin")

mongoengine.connect(
    db=MONGODB_DBNAME,
    username=MONGODB_CONNECTION_USERNAME,
    password=MONGODB_CONNECTION_PASSWORD,
    host=MONGODB_CONNECTION_HOST,
    port=MONGODB_CONNECTION_PORT,
    authentication_source=MONGODB_AUTHSRC,
)
