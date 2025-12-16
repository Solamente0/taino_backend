# apps/chat/apps.py
from django.apps import AppConfig


class AIChatConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai_chat"
    verbose_name = "چت با هوش مصنوعی"

    # def ready(self):
    #     try:
    #         import apps.ai_chat.signals
    #     except ImportError:
    #         pass
