from django.apps import AppConfig


class MessagingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.messaging"
    verbose_name = "پیغام ها"

    def ready(self):
        try:
            # Import signals
            import apps.messaging.signals

            # Initialize default SMS templates
            from apps.messaging.models import SystemSMSTemplate

            # SystemSMSTemplate.initialize_default_templates()
        except ImportError:
            print(f"Import Error!!!", flush=True)
            pass
