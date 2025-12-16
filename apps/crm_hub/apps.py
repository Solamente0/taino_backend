from django.apps import AppConfig


class CrmHubConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.crm_hub"
    verbose_name = "مدیریت ارتباط با مشتری (CRM)"

    def ready(self):
        """Import signals when app is ready"""
        try:
            import apps.crm_hub.signals
        except ImportError:
            pass

