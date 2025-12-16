# apps/file_to_text/apps.py
from django.apps import AppConfig


class FileToTextConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.file_to_text"
    verbose_name = "تبدیل فایل به متن"
