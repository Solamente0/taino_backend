# apps/chat/apps.py
from django.apps import AppConfig


class ChatConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.chat"
    verbose_name = "چت"

    # def ready(self):
    #     try:
    #         import apps.chat.signals
    #     except ImportError:
    #         pass
