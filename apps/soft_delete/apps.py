from django.apps import AppConfig


class SoftDeleteConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.soft_delete"
    verbose_name = "حذف نرم"

    def ready(self):
        from apps.soft_delete.signals import post_soft_delete, post_hard_delete, post_restore
