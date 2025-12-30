import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, "docker/.env"))

SECRET_KEY = env.str("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost"])

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "import_export",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "django_celery_results",
    "django_celery_beat",
    "apps.user.apps.UserConfig",
    "apps.country.apps.CountryConfig",
    "apps.initializers.apps.InitializersConfig",
    "apps.messaging.apps.MessagingConfig",
    "apps.authentication.apps.AuthenticationConfig",
    "apps.document.apps.DocumentConfig",
    "apps.banner.apps.BannerConfig",
    "apps.social_media.apps.SocialMediaConfig",
    "apps.version.apps.VersionConfig",
    "apps.ratelimit.apps.RatelimitConfig",
    "apps.referral.apps.ReferralConfig",
    "apps.feedback.apps.FeedbackConfig",
    "apps.payment.apps.PaymentConfig",
    "apps.wallet.apps.WalletConfig",
    "apps.address.apps.AddressConfig",
    "apps.setting.apps.SettingConfig",
    "apps.notification.apps.NotificationConfig",
    "apps.soft_delete.apps.SoftDeleteConfig",
    "apps.common.apps.CommonConfig",
    "apps.subscription.apps.SubscriptionConfig",
    "apps.permissions.apps.PermissionConfig",
    "apps.chat.apps.ChatConfig",
    "apps.ai_chat.apps.AIChatConfig",
    "apps.analyzer.apps.AnalyzerConfig",
    "apps.activity_log.apps.ActivityLogConfig",
    "apps.crm_hub.apps.CrmHubConfig",
    "apps.ai_support.apps.AiSupportConfig",
    "apps.file_to_text.apps.FileToTextConfig",
#    "apps.case.apps.CaseConfig",  # اضافه کنید
]

MIDDLEWARE = [
    # "django.middleware.cache.UpdateCacheMiddleware", # TODO: this must be enabled for better caching
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "base_utils.log.middlewares.RequestDetailMiddlewareLog",
    # "base_utils.middlewares.XSSProtectionMiddleware",
    "base_utils.middlewares.secretary.SecretaryMiddleware",
    "base_utils.middlewares.current_user.ThreadLocalUserMiddleware",
    # "base_utils.middlewares.SingleDeviceMiddleware",
    # "django.middleware.cache.FetchFromCacheMiddleware", # TODO: this must be enabled for better caching
    # "apps.activity_log.middleware.ActivityLogMiddleware",  # Add at the end
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        # 'ENGINE': 'django.contrib.gis.db.backends.postgis',
        "NAME": env.str("DB_CONNECTION_NAME", default="djangodb"),
        "USER": env.str("DB_CONNECTION_USER", default="dbuser"),
        "PASSWORD": env.str("DB_CONNECTION_PASSWORD", default="dbpasss"),
        "HOST": env.str("DB_CONNECTION_HOST", default="localhost"),
        "PORT": env.str("DB_CONNECTION_PORT", default="5432"),
        "ATOMIC_REQUESTS": env.bool("ATOMIC_REQUESTS", default=True),
        # Add these critical settings:
        "CONN_MAX_AGE": 600,  # Reuse connections for 60 seconds
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {"connect_timeout": 10, "options": "-c statement_timeout=30000"},  # 30 second query timeout
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Channel layers configuration (for WebSockets)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(env.str("REDIS_CONNECTION_HOST", "redis"), env.int("REDIS_CONNECTION_PORT", 6379))],
        },
    },
}

TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR.joinpath("staticfiles")  # Changed from "static" to "staticfiles"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static/"),
]
MEDIA_URL = "/ping/"
MEDIA_ROOT = BASE_DIR.joinpath("media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "authentication.TainoUser"


# djagno max file settings, django middlewares use it and raise exception
# Increase all upload limits
DATA_UPLOAD_MAX_MEMORY_SIZE = env.int("DATA_UPLOAD_MAX_MEMORY_SIZE", default=1024 * 1024 * 200)  # 200MB
FILE_UPLOAD_MAX_MEMORY_SIZE = DATA_UPLOAD_MAX_MEMORY_SIZE
UPLOAD_API_MAX_IMAGE_SIZE = env.int("UPLOAD_API_MAX_IMAGE_SIZE", default=1024 * 1024 * 100)  # 100MB
UPLOAD_API_MAX_VIDEO_SIZE = env.int("UPLOAD_API_MAX_VIDEO_SIZE", default=1024 * 1024 * 500)  # 500MB
UPLOAD_API_MAX_DOCUMENT_SIZE = env.int("UPLOAD_API_MAX_DOCUMENT_SIZE", default=1024 * 1024 * 200)  # 200MB

PROD_ADMIN_PATH = env.str("PROD_ADMIN_PATH", "admin")

GOOGLE_AUTH_CONFIG = {
    "GOOGLE_OAUTH2_APP_URL": env.str("GOOGLE_OAUTH2_APP_URL", "http://localhost"),
    "GOOGLE_OAUTH2_API_URL": env.str("GOOGLE_OAUTH2_API_URL", "http://localhost"),
    "GOOGLE_OAUTH2_LOGIN_URL": f"{env.str('GOOGLE_OAUTH2_APP_URL', 'http://localhost')}/internal/login",
    "GOOGLE_OAUTH2_CLIENT_ID": env.str("GOOGLE_OAUTH2_CLIENT_ID", "dummy"),
    "GOOGLE_OAUTH2_CLIENT_SECRET": env.str("GOOGLE_OAUTH2_CLIENT_SECRET", "dummy"),
    "GOOGLE_ACCESS_TOKEN_OBTAIN_URL": "https://oauth2.googleapis.com/token",
    "GOOGLE_USER_INFO_URL": "https://www.googleapis.com/oauth2/v3/userinfo",
}
