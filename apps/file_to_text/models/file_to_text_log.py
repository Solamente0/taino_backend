# apps/file_to_text/models/file_to_text_log.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, ActivableModel, AdminStatusModel

User = get_user_model()


class FileToTextLog(TimeStampModel, ActivableModel, AdminStatusModel):
    """
    Model to store file to text ctainoersion logs
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="file_to_text_logs", 
        verbose_name=_("کاربر")
    )
    
    original_filename = models.CharField(
        max_length=255,
        verbose_name=_("نام فایل اصلی")
    )
    
    extracted_text = models.TextField(
        verbose_name=_("متن استخراج شده"),
        null=True,
        blank=True
    )
    
    file_type = models.CharField(
        max_length=50,
        verbose_name=_("نوع فایل"),
        null=True,
        blank=True
    )
    
    file_size = models.IntegerField(
        verbose_name=_("حجم فایل (بایت)"),
        null=True,
        blank=True
    )
    
    ai_type = models.CharField(
        max_length=50,
        default="file_to_text",
        null=True,
        blank=True,
        verbose_name=_("نوع سرویس")
    )
    
    coins_used = models.IntegerField(
        verbose_name=_("تعداد سکه استفاده شده"),
        default=0
    )
    
    character_count = models.IntegerField(
        verbose_name=_("تعداد کاراکتر"),
        default=0
    )
    
    word_count = models.IntegerField(
        verbose_name=_("تعداد کلمات"),
        default=0
    )

    class Meta:
        verbose_name = _("گزارش تبدیل فایل به متن")
        verbose_name_plural = _("گزارش‌های تبدیل فایل به متن")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["ai_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"File to Text for {self.user} - {self.original_filename}"
