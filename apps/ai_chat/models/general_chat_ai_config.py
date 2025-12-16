# apps/ai_chat/models/general_chat_ai_config.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from base_utils.base_models import (
    TimeStampModel,
    ActivableModel,
    AdminStatusModel,
    CreatorModel,
    StaticalIdentifier,
)


class GeneralChatAIConfig(TimeStampModel, ActivableModel, AdminStatusModel, CreatorModel, StaticalIdentifier):
    """
    General AI Chat Configuration - Categories like 'دادخواست بدوی'
    This is the parent configuration that contains common settings
    """

    name = models.CharField(max_length=200, verbose_name=_("نام دسته‌بندی"))
    description = models.TextField(verbose_name=_("توضیحات"))

    # System instruction specific to this category
    system_instruction = models.TextField(
        verbose_name=_("دستورالعمل سیستمی"), help_text=_("این دستورالعمل با دستورالعمل ChatAIConfig ترکیب می‌شود")
    )

    # Chat limitations
    max_messages_per_chat = models.PositiveIntegerField(default=10, verbose_name=_("حداکثر تعداد پیام در هر چت"))
    max_tokens_per_chat = models.PositiveIntegerField(default=20000, verbose_name=_("حداکثر توکن در هر چت"))
    form_schema = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        verbose_name=_("طرح فرم دینامیک"),
    )

    # Display order
    order = models.PositiveIntegerField(default=0, verbose_name=_("ترتیب نمایش"))

    # Icon or image
    icon = models.ImageField(upload_to="ai_config_icons/", null=True, blank=True, verbose_name=_("آیکون"))

    class Meta:
        verbose_name = _("پیکربندی عمومی هوش مصنوعی")
        verbose_name_plural = _("پیکربندی‌های عمومی هوش مصنوعی")
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.name

    # def clean(self):
    #     """Validate form_schema structure"""
    #     super().clean()
    #     if self.form_schema:
    #         try:
    #             self._validate_form_schema(self.form_schema)
    #         except Exception as e:
    #             raise ValidationError({
    #                 'form_schema': f'Invalid schema structure: {str(e)}'
    #             })
    #
    # def _validate_form_schema(self, schema):
    #     """Validate the JSON schema structure"""
    #     if not isinstance(schema, dict):
    #         raise ValidationError("Schema must be a dictionary")
    #
    #     # Validate required top-level keys
    #     if 'sections' not in schema:
    #         raise ValidationError("Schema must contain 'sections' key")
    #
    #     if not isinstance(schema['sections'], list):
    #         raise ValidationError("'sections' must be a list")
    #
    #     # Validate each section
    #     valid_types = [
    #         'party_list', 'text', 'textarea', 'number',
    #         'checkbox', 'radio', 'select', 'date',
    #         'file_upload', 'custom'
    #     ]
    #
    #     for section in schema['sections']:
    #         if 'id' not in section or 'type' not in section:
    #             raise ValidationError("Each section must have 'id' and 'type'")
    #
    #         if section['type'] not in valid_types:
    #             raise ValidationError(f"Invalid section type: {section['type']}")
