# apps/ai_support/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

from base_utils.base_models import (
    TimeStampModel,
    ActivableModel,
    AdminStatusModel,
    CreatorModel,
)

User = get_user_model()


class SupportSessionStatusEnum(models.TextChoices):
    ACTIVE = "active", _("فعال")
    CLOSED = "closed", _("بسته شده")


class SupportMessageTypeEnum(models.TextChoices):
    TEXT = "text", _("متن")
    IMAGE = "image", _("تصویر")
    FILE = "file", _("فایل")


class SupportAIConfig(TimeStampModel, ActivableModel, AdminStatusModel, CreatorModel):
    """Configuration for AI support chatbot"""
    
    name = models.CharField(
        max_length=100,
        verbose_name=_("نام پیکربندی")
    )
    
    # OpenRouter Configuration
    api_key = models.CharField(
        max_length=255,
        verbose_name=_("کلید API OpenRouter"),
        help_text=_("کلید API از openrouter.ai")
    )
    
    base_url = models.URLField(
        default="https://openrouter.ai/api/v1",
        verbose_name=_("آدرس پایه API")
    )
    
    model_name = models.CharField(
        max_length=200,
        default="meta-llama/llama-3.1-8b-instruct:free",
        verbose_name=_("نام مدل"),
        help_text=_("مثال: meta-llama/llama-3.1-8b-instruct:free")
    )
    
    # System Instructions
    system_prompt = models.TextField(
        verbose_name=_("دستورالعمل سیستمی"),
        help_text=_("دستورالعمل‌هایی که به هوش مصنوعی داده می‌شود"),
        default="""شما یک دستیار پشتیبانی حرفه‌ای هستید که به فارسی پاسخ می‌دهید.
وظیفه شما کمک به کاربران در حل مشکلات و پاسخ به سوالات آنهاست.
همیشه مودب، صبور و دقیق باشید.
اگر نمی‌دانید، صادقانه بگویید که این موضوع را به تیم فنی ارجاع می‌دهید."""
    )
    
    # Model Parameters
    temperature = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0.0), MaxValueValidator(2.0)],
        verbose_name=_("دما (Temperature)"),
        help_text=_("مقدار بین 0 تا 2. مقادیر پایین‌تر: پاسخ‌های قطعی‌تر، مقادیر بالاتر: پاسخ‌های خلاقانه‌تر")
    )
    
    max_tokens = models.PositiveIntegerField(
        default=500,
        validators=[MinValueValidator(100), MaxValueValidator(4000)],
        verbose_name=_("حداکثر توکن"),
        help_text=_("حداکثر طول پاسخ (تعداد کلمات تقریبی)")
    )
    
    ctainoersation_history_limit = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        verbose_name=_("تعداد پیام‌های تاریخچه"),
        help_text=_("تعداد پیام‌های قبلی که به عنوان زمینه به AI ارسال می‌شود")
    )
    
    # Fallback message
    fallback_message = models.TextField(
        default="متاسفانه در حال حاضر قادر به پاسخگویی نیستم. لطفاً بعداً دوباره تلاش کنید.",
        verbose_name=_("پیام خطا"),
        help_text=_("پیامی که در صورت خطا نمایش داده می‌شود")
    )
    
    # Response settings
    response_delay_seconds = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(10)],
        verbose_name=_("تاخیر پاسخ (ثانیه)"),
        help_text=_("تاخیر مصنوعی قبل از ارسال پاسخ (برای طبیعی‌تر بودن)")
    )
    
    # Active configuration
    is_default = models.BooleanField(
        default=False,
        verbose_name=_("پیکربندی پیش‌فرض"),
        help_text=_("این پیکربندی به عنوان پیش‌فرض استفاده شود؟")
    )
    
    # Usage tracking
    total_requests = models.PositiveIntegerField(
        default=0,
        verbose_name=_("تعداد کل درخواست‌ها")
    )
    
    total_errors = models.PositiveIntegerField(
        default=0,
        verbose_name=_("تعداد کل خطاها")
    )
    
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("آخرین استفاده")
    )
    
    class Meta:
        verbose_name = _("پیکربندی هوش مصنوعی پشتیبانی")
        verbose_name_plural = _("پیکربندی‌های هوش مصنوعی پشتیبانی")
        ordering = ["-is_default", "-created_at"]
    
    def __str__(self):
        return f"{self.name} {'(پیش‌فرض)' if self.is_default else ''}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default configuration
        if self.is_default:
            SupportAIConfig.objects.filter(
                is_default=True,
                is_active=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_active_config(cls):
        """Get the active configuration (default or first active)"""
        # Try to get default config
        config = cls.objects.filter(is_default=True, is_active=True).first()
        
        # If no default, get the first active config
        if not config:
            config = cls.objects.filter(is_active=True).first()
        
        return config
    
    def increment_usage(self):
        """Increment usage counter"""
        from django.utils import timezone
        self.total_requests += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=["total_requests", "last_used_at"])
    
    def increment_errors(self):
        """Increment error counter"""
        self.total_errors += 1
        self.save(update_fields=["total_errors"])


class SupportSession(TimeStampModel, ActivableModel, AdminStatusModel):
    """Support chat session"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="support_sessions",
        verbose_name=_("کاربر")
    )
    
    status = models.CharField(
        max_length=20,
        choices=SupportSessionStatusEnum.choices,
        default=SupportSessionStatusEnum.ACTIVE,
        verbose_name=_("وضعیت")
    )
    
    subject = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("موضوع")
    )
    
    unread_messages = models.IntegerField(
        default=0,
        verbose_name=_("پیام‌های خوانده نشده")
    )
    
    total_messages = models.PositiveIntegerField(
        default=0,
        verbose_name=_("تعداد کل پیام‌ها")
    )
    
    class Meta:
        verbose_name = _("جلسه پشتیبانی")
        verbose_name_plural = _("جلسات پشتیبانی")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["status"]),
        ]
    
    def __str__(self):
        return f"Support Session {self.pid} - {self.user}"
    
    def mark_all_read(self):
        """Mark all messages as read"""
        self.unread_messages = 0
        self.save(update_fields=["unread_messages"])
        self.messages.filter(is_read=False).update(is_read=True)


class SupportMessage(TimeStampModel, ActivableModel, AdminStatusModel):
    """Support chat message"""
    
    session = models.ForeignKey(
        SupportSession,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name=_("جلسه پشتیبانی")
    )
    
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="support_messages",
        verbose_name=_("فرستنده")
    )
    
    message_type = models.CharField(
        max_length=20,
        choices=SupportMessageTypeEnum.choices,
        default=SupportMessageTypeEnum.TEXT,
        verbose_name=_("نوع پیام")
    )
    
    content = models.TextField(verbose_name=_("محتوا"))
    
    attachment = models.ForeignKey(
        "document.TainoDocument",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_attachments",
        verbose_name=_("فایل پیوست")
    )
    
    is_ai = models.BooleanField(
        default=False,
        verbose_name=_("پیام هوش مصنوعی")
    )
    
    is_read = models.BooleanField(
        default=False,
        verbose_name=_("خوانده شده")
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("زمان خواندن")
    )
    
    class Meta:
        verbose_name = _("پیام پشتیبانی")
        verbose_name_plural = _("پیام‌های پشتیبانی")
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["session"]),
            models.Index(fields=["sender"]),
            models.Index(fields=["is_read"]),
        ]
    
    def __str__(self):
        return f"Message from {self.sender} at {self.created_at}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        if is_new:
            session = self.session
            if self.sender == session.user and not self.is_ai:
                self.is_read = True
            else:
                session.unread_messages += 1
            
            session.total_messages += 1
            session.save(update_fields=["unread_messages", "total_messages"])
        
        super().save(*args, **kwargs)
