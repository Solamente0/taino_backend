from django.apps import AppConfig


class NotificationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notification"
    verbose_name = "اعلانات"

    def ready(self):
        # fmt: off
        # from .signals import delete_requests_after_agency_request_deleted,delete_requests_after_coworker_request_deleted  # noqa
        # fmt: on
        pass
