from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.authentication"
    verbose_name = "احراز هویت"

    def ready(self):
        try:
            import apps.authentication.signals  # Import signals when app is ready
        except ImportError:
            pass
