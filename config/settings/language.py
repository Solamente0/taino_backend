from django.db import models

from .base import BASE_DIR

# LANGUAGE_CODE = "en"  # default of system
LANGUAGE_CODE = "fa"


class AvailableLanguageChoices(models.TextChoices):
    ENGLISH = "en", "English"
    PERSIAN = "fa", "Persian"


LANGUAGES = AvailableLanguageChoices.choices

LOCALE_PATHS = [
    str(BASE_DIR / "locale/"),
]
