from django.apps import AppConfig


class SettingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.setting"
    verbose_name = "تنظیمات"

    def ready(self):
        import apps.setting.signals  # Import signals when app is ready
