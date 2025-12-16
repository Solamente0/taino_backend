from .base import env

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env.str("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.str("EMAIL_PORT", default="587")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)

EMAIL_HOST_USER = env.str("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD")

SMS_IR_API_KEY = env.str("SMS_IR_API_KEY", default="dummy api key")
SMS_TR_API_ID = env.str("SMS_TR_API_ID", default="dummy api key")
SMS_TR_API_KEY = env.str("SMS_TR_API_KEY", default="dummy api key")
