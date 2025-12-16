from .base import DEBUG, env, DATABASES
from .third_party import REST_FRAMEWORK, REDIS_HOST, REDIS_PORT

# todo add allowed hosts and CORS settings that you want
if not DEBUG:
    ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*.taino.ir", ".taino.ir", "localhost", "127.0.0.1"])

    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = "DENY"

    SESSION_COOKIE_SAMESITE = "None"  # Required for cross-site cookies
    CSRF_COOKIE_SAMESITE = "None"  # If using CSRF

    REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ]
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
        "config.renderer.CustomJSONRenderer",
    ]
    #
    # CORS_ALLOW_ALL_ORIGINS = False  # Be explicit about allowed origins
    # CORS_ALLOW_CREDENTIALS = True
    # # Critical for OPTIONS preflight requests
    # CORS_ALLOW_METHODS = [
    #     "DELETE",
    #     "GET",
    #     "OPTIONS",
    #     "PATCH",
    #     "POST",
    #     "PUT",
    # ]
    #
    # CORS_ALLOW_HEADERS = [
    #     "accept",
    #     "accept-encoding",
    #     "authorization",
    #     "content-type",
    #     "dnt",
    #     "origin",
    #     "user-agent",
    #     "x-csrftoken",
    #     "x-requested-with",
    #     "access-control-allow-origin",
    # ]
    #
    # # Important - allow preflight requests to be cached
    # CORS_PREFLIGHT_MAX_AGE = 86400  # 24 hours
    #
    # CORS_ALLOWED_ORIGIN_REGEXES = [
    #     r"^https:\/\/[a-z][a-z0-9_]*(\.[a-z0-9_]+)*\.taino\.ir",
    #     r"https:\/\/(?:[a-zA-Z0-9-]+\.)*taino\.ir",
    #     "localhost",
    #     r"^http://\w+\.localhost$",
    #     r"^http://localhost:3000",
    #     r"^http://localhost:8089",
    #     r"^https://localhost:443",
    #     r"^https://localhost:4443",
    #     r"^http://localhost:8000",
    #     r"^http://localhost:80",
    #     r"http://api.taino.ir",
    #     r"https://api.taino.ir",
    #     r"https//taino.ir",
    #     r"http//taino.ir",
    # ]
    #
    # CSRF_TRUSTED_ORIGINS = [
    #     # "http://localhost:8080",
    #     # "http://localhost:8000",
    #     # "http://127.0.0.1:8000",
    #     # "http://localhost:3000",
    #     # "http://localhost:*",
    #     # "http://127.0.0.1:*",
    #     # "http://127.0.0.1:8080",
    #     # "http://127.0.0.1:3000",
    #     # "http://127.0.0.1:3000",
    #     # "http://localhost:3000",
    #     "https://*.taino.ir",
    #     "https://*.127.0.0.1",
    #     "https://api.taino.ir",
    #     "http://api.taino.ir",
    #     "https://*.taino.ir",
    # ]
    # CORS_ALLOWED_ORIGINS = (
    #     "http://localhost:3000",
    #     "http://localhost:5173",
    #     "http://127.0.0.1:5173",
    #     "http://127.0.0.1:8000",
    #     "http://127.0.0.1:3000",
    #     "https://127.0.0.1:5173",
    #     "https://127.0.0.1:3000",
    #     "https://localhost:5173",
    #     "https://localhost:8000",
    #     "https://localhost:3000",
    #     "https://taino.ir",
    #     "http://taino.ir",
    #     "https://api.taino.ir",
    #     "http://api.taino.ir",
    # )
    # # CSRF_COOKIE_DOMAIN = env("CSRF_COOKIE_DOMAIN", default=".taino.ir")
    #
    # CSRF_WHITELIST_ORIGINS = [
    #     "localhost:3000",
    #     "localhost:8080",
    #     "localhost:8000",
    #     "taino.ir",
    #     ".taino.ir",
    # ]

    # TODO: This must change due to using cookies in the future!

    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ORIGIN_ALLOW_ALL = True
    CORS_ALLOW_CREDENTIALS = True

    CORS_ALLOWED_ORIGINS = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
        "https://127.0.0.1:5173",
        "https://127.0.0.1:3000",
        "https://localhost:5173",
        "https://localhost:8000",
        "https://localhost:3000",
        "https://taino.ir",
        "http://taino.ir",
        "https://api.taino.ir",
        "http://api.taino.ir",
        "http://dev-front-5443.taino.ir",
        "https://dev-front-5443.taino.ir",
        "https://dev-api-5443.taino.ir",
        "http://dev-api-5443.taino.ir",
    )
    CORS_ALLOWED_ORIGIN_REGEXES = [
        r"^http://\w+\.localhost$",
        r"^http://localhost:5178$",
        r"^http://localhost:5178",
        r"^http://localhost:3000",
        r"^http://localhost:8000",
        r"http://api.taino.ir",
        r"https://api.taino.ir",
        r"https//taino.ir",
        r"http//taino.ir",
        r"^http:\/\/dev-front-\d+\.taino\.ir$",
        r"^https:\/\/dev-front-\d+\.taino\.ir$",
    ]

    CORS_ORIGIN_WHITELIST = (
        "http://localhost:5173",
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "https://api.taino.ir",
        "http://api.taino.ir",
        "http://taino.ir",
        "https://taino.ir",
        "http://dev-front-5443.taino.ir",
        "https://dev-front-5443.taino.ir",
    )

    CORS_ALLOW_METHODS = [
        "DELETE",
        "GET",
        "OPTIONS",
        "PATCH",
        "POST",
        "PUT",
    ]
    CORS_ALLOW_HEADERS = [
        "accept",
        "accept-encoding",
        "authorization",
        "content-type",
        "dnt",
        "origin",
        "user-agent",
        "x-csrftoken",
        "x-requested-with",
        "access-control-allow-origin",
    ]

    CSRF_TRUSTED_ORIGINS = [
        "http://localhost:8080",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://localhost:*",
        "http://127.0.0.1:*",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "https://*.taino.ir",
        "https://*.127.0.0.1",
        "https://api.taino.ir",
        "http://api.taino.ir",
        "https://*.taino.ir",
        "https://dev-front-5443.taino.ir",
        "https://dev-api-5443.taino.ir",
        "http://dev-front-5443.taino.ir",
        "http://dev-api-5443.taino.ir",
    ]

    # CSRF_COOKIE_DOMAIN = env("CSRF_COOKIE_DOMAIN", default=".taino.ir")

    CSRF_WHITELIST_ORIGINS = [
        "localhost:3000",
        "localhost:8080",
        "localhost:8000",
        "taino.ir",
        ".taino.ir",
    ]

    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "IGNORE_EXCEPTIONS": True,
            },
        }
    }
    # Cache settings
    CACHE_MIDDLEWARE_ALIAS = "default"
    CACHE_MIDDLEWARE_SECONDS = 600
    CACHE_MIDDLEWARE_KEY_PREFIX = "taino"
    DATABASES["default"]["CONN_MAX_AGE"] = 600  # 10 minutes
    DATABASES["default"]["CONN_HEALTH_CHECKS"] = True  # Keep this
    DATABASES["default"]["OPTIONS"] = {
        "connect_timeout": 10,
        "options": "-c statement_timeout=60000",  # ✅ Increase from 30s to 60s
        "keepalives": 1,  # ✅ Add keepalive
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }
