"""
apps/activity_log/models.py
Activity logging model for tracking user actions
"""
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from base_utils.base_models import TimeStampModel, BaseModel

User = get_user_model()


class ActivityLogAction(models.TextChoices):
    """Common activity actions"""
    # Authentication
    LOGIN = "login", "ورود"
    LOGOUT = "logout", "خروج"
    REGISTER = "register", "ثبت‌نام"

    # CRUD Operations
    CREATE = "create", "ایجاد"
    READ = "read", "مشاهده"
    UPDATE = "update", "ویرایش"
    DELETE = "delete", "حذف"

    # File Operations
    UPLOAD = "upload", "آپلود"
    DOWNLOAD = "download", "دانلود"

    # Payment
    PAYMENT_INITIATED = "payment_initiated", "شروع پرداخت"
    PAYMENT_SUCCESS = "payment_success", "پرداخت موفق"
    PAYMENT_FAILED = "payment_failed", "پرداخت ناموفق"

    # Subscription
    SUBSCRIPTION_PURCHASED = "subscription_purchased", "خرید اشتراک"
    SUBSCRIPTION_EXPIRED = "subscription_expired", "انقضای اشتراک"

    # AI Chat
    AI_CHAT_STARTED = "ai_chat_started", "شروع چت هوش مصنوعی"
    AI_CHAT_MESSAGE = "ai_chat_message", "پیام چت هوش مصنوعی"

    # Document
    DOCUMENT_ANALYZED = "document_analyzed", "تحلیل سند"

    # Notification
    NOTIFICATION_SENT = "notification_sent", "ارسال اعلان"
    NOTIFICATION_READ = "notification_read", "خواندن اعلان"

    # Court
    COURT_NOTIFICATION_CREATED = "court_notification_created", "ایجاد اطلاعیه دادگاه"
    COURT_CALENDAR_EVENT_CREATED = "court_calendar_event_created", "ایجاد رویداد تقویم دادگاه"

    # Wallet
    WALLET_CHARGE = "wallet_charge", "شارژ کیف پول"
    WALLET_DEBIT = "wallet_debit", "برداشت از کیف پول"

    # Profile
    PROFILE_UPDATED = "profile_updated", "ویرایش پروفایل"
    PASSWORD_CHANGED = "password_changed", "تغییر رمز عبور"

    # Device
    DEVICE_REGISTERED = "device_registered", "ثبت دستگاه"
    DEVICE_DEACTIVATED = "device_deactivated", "غیرفعال‌سازی دستگاه"

    # Other
    EXPORT = "export", "خروجی"
    IMPORT = "import", "ورودی"
    SEARCH = "search", "جستجو"
    FILTER = "filter", "فیلتر"
    OTHER = "other", "سایر"


class ActivityLogLevel(models.TextChoices):
    """Log levels for categorizing activities"""
    DEBUG = "debug", "اشکال‌زدایی"
    INFO = "info", "اطلاعات"
    WARNING = "warning", "هشدار"
    ERROR = "error", "خطا"
    CRITICAL = "critical", "بحرانی"


class ActivityLog(TimeStampModel):
    """
    Model for tracking all user activities in the system.
    Automatically deleted after 10 days via Celery task.
    """

    # User who performed the action
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="activity_logs",
        null=True,
        blank=True,
        help_text="کاربری که عملیات را انجام داده"
    )

    # Action details
    action = models.CharField(
        max_length=50,
        choices=ActivityLogAction.choices,
        db_index=True,
        help_text="نوع عملیات انجام شده"
    )

    level = models.CharField(
        max_length=20,
        choices=ActivityLogLevel.choices,
        default=ActivityLogLevel.INFO,
        db_index=True,
        help_text="سطح اهمیت لاگ"
    )

    # Description
    description = models.TextField(
        blank=True,
        help_text="توضیحات تکمیلی درباره عملیات"
    )

    # Related object (optional)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="نوع مدل مرتبط"
    )
    object_id = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="شناسه شیء مرتبط"
    )
    content_object = GenericForeignKey('content_type', 'object_id')

    # Request metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="آدرس IP کاربر"
    )

    user_agent = models.TextField(
        blank=True,
        help_text="User Agent مرورگر"
    )

    endpoint = models.CharField(
        max_length=500,
        blank=True,
        help_text="مسیر API که فراخوانی شده"
    )

    method = models.CharField(
        max_length=10,
        blank=True,
        help_text="متد HTTP (GET, POST, etc.)"
    )

    # Additional data
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="داده‌های اضافی به صورت JSON"
    )

    # Device information
    device_id = models.CharField(
        max_length=128,
        blank=True,
        help_text="شناسه دستگاه"
    )

    # Status
    is_successful = models.BooleanField(
        default=True,
        help_text="آیا عملیات موفقیت‌آمیز بوده است"
    )

    error_message = models.TextField(
        blank=True,
        help_text="پیغام خطا در صورت عدم موفقیت"
    )

    class Meta:
        verbose_name = "لاگ فعالیت"
        verbose_name_plural = "لاگ‌های فعالیت"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
            models.Index(fields=["level", "-created_at"]),
            models.Index(fields=["is_successful", "-created_at"]),
        ]

    def __str__(self):
        user_str = f"{self.user}" if self.user else "Anonymous"
        return f"{user_str} - {self.get_action_display()} - {self.created_at}"

    @property
    def age_in_days(self):
        """Calculate how old this log is in days"""
        from django.utils import timezone
        age = timezone.now() - self.created_at
        return age.days
