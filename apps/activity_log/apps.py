# apps/activity_log/apps.py
from django.apps import AppConfig


class ActivityLogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.activity_log"
    verbose_name = "لاگ فعالیت"
