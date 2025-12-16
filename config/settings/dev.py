from .base import DEBUG, INSTALLED_APPS
from .third_party import REST_FRAMEWORK


if DEBUG:

    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    # SECURE_SSL_REDIRECT = True

    INSTALLED_APPS += [
        "drf_spectacular",
        "drf_spectacular_sidecar",
    ]

    REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ]
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
        "config.renderer.CustomJSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ]

    # TODO: this must change due to using cookies in the future

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

    # REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"] = "drf_spectacular.openapi.AutoSchema"
    REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"] = "config.swagger.CustomAutoSchema"
    SPECTACULAR_SETTINGS = {
        "TITLE": "Tainoekalat API SWAGGER",
        "SERVE_INCLUDE_SCHEMA": False,
        "SWAGGER_UI_DIST": "SIDECAR",
        "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
        "REDOC_DIST": "SIDECAR",
        "SWAGGER_UI_SETTINGS": {
            "deepLinking": True,
            "persistAuthorization": True,
            "displayOperationId": True,
            "docExpansion": "none",
            "requestSnippetsEnabled": True,
            "displayRequestDuration": True,
        },
    }
