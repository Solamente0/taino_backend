# apps/ai_chat/models/ai_session.py

from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import (
    TimeStampModel,
    ActivableModel,
    AdminStatusModel,
    CreatorModel,
    BoundaryDateModel,
)

User = get_user_model()


class AISessionStatusEnum(models.TextChoices):
    PENDING = "pending", _("در انتظار")
    ACTIVE = "active", _("فعال")
    COMPLETED = "completed", _("تکمیل شده")
    EXPIRED = "expired", _("منقضی شده")
    CANCELLED = "cancelled", _("لغو شده")


class AITypeEnum(models.TextChoices):
    V = "v", _("هوش مصنوعی V")
    V_PLUS = "v_plus", _("هوش مصنوعی V+")
    V_X = "v_x", _("هوش مصنوعی VX")
    V_PLUS_PRO = "v_plus_pro", _("هوش مصنوعی V Plus Pro")
    V_X_PRO = "v_x_pro", _("هوش مصنوعی VX Pro")


class AISession(TimeStampModel, BoundaryDateModel, ActivableModel, AdminStatusModel, CreatorModel):
    """مدل جلسه چت با هوش مصنوعی"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_ai_sessions", verbose_name=_("کاربر"))

    ai_config = models.ForeignKey(
        "ChatAIConfig",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_sessions",
        verbose_name=_("تنظیمات هوش مصنوعی"),
    )

    status = models.CharField(
        max_length=20, choices=AISessionStatusEnum.choices, default=AISessionStatusEnum.ACTIVE, verbose_name=_("وضعیت")
    )

    title = models.CharField(max_length=255, verbose_name=_("عنوان"))

    ai_type = models.CharField(
        max_length=20, choices=AITypeEnum.choices, default=AITypeEnum.V, verbose_name=_("نوع هوش مصنوعی")
    )

    # ═══════════════════════════════════════════════════════════
    # ردیابی استفاده
    # ═══════════════════════════════════════════════════════════

    # توکن‌ها (برای گزارش‌دهی، حتی در قیمت‌گذاری پیام‌محور)
    total_input_tokens = models.PositiveIntegerField(default=0, verbose_name=_("مجموع توکن‌های ورودی"))
    total_output_tokens = models.PositiveIntegerField(default=0, verbose_name=_("مجموع توکن‌های خروجی"))
    total_tokens_used = models.PositiveIntegerField(default=0, verbose_name=_("مجموع توکن‌های استفاده شده"))

    # کاراکترها (برای قیمت‌گذاری هیبریدی)
    total_characters_sent = models.PositiveIntegerField(default=0, verbose_name=_("مجموع کاراکترهای ارسالی"))

    # هزینه
    total_cost_coins = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("هزینه کل (سکه)"))

    # تعداد پیام‌ها
    total_messages = models.PositiveIntegerField(default=0, verbose_name=_("تعداد کل پیام‌ها"))
    unread_messages = models.IntegerField(default=0, verbose_name=_("پیامهای خوانده نشده"))

    # ═══════════════════════════════════════════════════════════
    # پارامترهای فرانت‌اند
    # ═══════════════════════════════════════════════════════════

    temperature = models.FloatField(null=True, blank=True, verbose_name=_("دما"))
    max_tokens = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("حداکثر توکن"))

    # ═══════════════════════════════════════════════════════════
    # کانتکست و وضعیت
    # ═══════════════════════════════════════════════════════════

    ai_context = models.JSONField(null=True, blank=True, verbose_name=_("کانتکست هوش مصنوعی"))

    is_readonly = models.BooleanField(default=False, verbose_name=_("فقط خواندنی"))
    readonly_reason = models.CharField(max_length=100, null=True, blank=True, verbose_name=_("دلیل فقط خواندنی"))

    paid_with_coins = models.BooleanField(default=True, verbose_name=_("با سکه پرداخت شده؟"))

    duration_minutes = models.IntegerField(default=10, verbose_name=_("مدت زمان چت"))

    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("مبلغ"))

    # ═══════════════════════════════════════════════════════════
    # فیلدهای ویژه قیمت‌گذاری هیبریدی پیشرفته
    # ═══════════════════════════════════════════════════════════

    # آیا هزینه پایه پرداخت شده؟
    hybrid_base_cost_paid = models.BooleanField(default=False, verbose_name=_("هزینه پایه پرداخت شده"))

    # تعداد کاراکترهای رایگان استفاده شده
    hybrid_free_chars_used = models.PositiveIntegerField(default=0, verbose_name=_("کاراکترهای رایگان مصرف شده"))

    class Meta:
        verbose_name = _("جلسه هوش مصنوعی")
        verbose_name_plural = _("جلسات هوش مصنوعی")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.user}"

    # ═══════════════════════════════════════════════════════════
    # متدهای کمکی
    # ═══════════════════════════════════════════════════════════

    def check_and_update_readonly(self):
        """بررسی و بروزرسانی وضعیت readonly بر اساس محدودیت‌ها"""
        if self.is_readonly:
            return True, self.readonly_reason

        if not self.ai_config or not self.ai_config.general_config:
            return False, None

        general_config = self.ai_config.general_config

        # بررسی محدودیت پیام
        if self.total_messages >= general_config.max_messages_per_chat:
            self.is_readonly = True
            self.readonly_reason = "max_messages_reached"
            self.status = AISessionStatusEnum.COMPLETED
            self.save()
            return True, "حداکثر تعداد پیام‌ها"

        # بررسی محدودیت توکن
        if self.total_tokens_used >= general_config.max_tokens_per_chat:
            self.is_readonly = True
            self.readonly_reason = "max_tokens_reached"
            self.status = AISessionStatusEnum.COMPLETED
            self.save()
            return True, "حداکثر تعداد توکن‌ها"

        return False, None

    def add_message_based_cost(self, cost: float):
        """
        افزودن هزینه پیام‌محور
        این متد همان add_message_based_cost است که قبلاً تعریف شده
        این alias برای سازگاری با transaction_tracking اضافه شده

        Args:
            cost: هزینه به سکه
        """
        self.add_message_based_cost(cost)

    def add_hybrid_usage(self, character_count: int, input_tokens: int, output_tokens: int, cost_breakdown: dict):
        """
        افزودن استفاده هیبریدی

        Args:
            character_count: تعداد کاراکترهای ارسالی
            input_tokens: توکن‌های ورودی
            output_tokens: توکن‌های خروجی
            cost_breakdown: جزئیات هزینه از calculate_advanced_hybrid_cost
        """
        # بروزرسانی کاراکترها
        self.total_characters_sent += character_count

        # بروزرسانی توکن‌ها
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_tokens_used = self.total_input_tokens + self.total_output_tokens

        # بروزرسانی هزینه پایه
        if not self.hybrid_base_cost_paid and cost_breakdown.get("base_cost", 0) > 0:
            self.hybrid_base_cost_paid = True

        # بروزرسانی کاراکترهای رایگان
        self.hybrid_free_chars_used += cost_breakdown.get("free_chars_used", 0)

        # بروزرسانی هزینه کل
        self.total_cost_coins += Decimal(str(cost_breakdown.get("total_cost", 0)))

        self.save()
        self.check_and_update_readonly()

    def add_token_usage(self, input_tokens: int, output_tokens: int):
        """
        افزودن استفاده توکن (برای گزارش‌دهی)

        Args:
            input_tokens: توکن‌های ورودی
            output_tokens: توکن‌های خروجی
        """
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_tokens_used = self.total_input_tokens + self.total_output_tokens
        self.save()
        self.check_and_update_readonly()

    def calculate_estimated_next_cost(self) -> dict:
        """
        تخمین هزینه پیام بعدی

        Returns:
            dict با اطلاعات هزینه
        """
        if not self.ai_config:
            return {"estimated_cost": 0, "pricing_type": "unknown"}

        if self.ai_config.is_message_based_pricing():
            return {
                "estimated_cost": float(self.ai_config.cost_per_message),
                "pricing_type": "message_based",
                "currency": "coins",
            }

        elif self.ai_config.is_advanced_hybrid_pricing():
            # برای هیبریدی، تخمین بر اساس میانگین
            avg_chars = 0
            if self.total_messages > 0:
                avg_chars = self.total_characters_sent // self.total_messages
            else:
                avg_chars = 1000  # پیش‌فرض

            # استفاده از max_tokens فعلی جلسه
            max_tokens = self.max_tokens or self.ai_config.hybrid_tokens_min

            # محاسبه با در نظر گرفتن اینکه هزینه پایه پرداخت شده
            cost_info = self.ai_config.calculate_advanced_hybrid_cost(
                character_count=avg_chars, max_tokens_requested=max_tokens
            )

            # اگر هزینه پایه قبلاً پرداخت شده، آن را کم کنیم
            if self.hybrid_base_cost_paid:
                cost_info["base_cost"] = 0
                cost_info["total_cost"] = cost_info["char_cost"] + cost_info["step_cost"]

            return {
                "estimated_cost": cost_info["total_cost"],
                "pricing_type": "advanced_hybrid",
                "currency": "coins",
                "breakdown": cost_info,
            }

        return {"estimated_cost": 0, "pricing_type": "unknown"}

    def get_transaction_summary(self) -> dict:
        """
        خلاصه تراکنش‌های جلسه

        Returns:
            dict با اطلاعات تراکنش‌ها
        """
        return {
            "session_pid": str(self.pid),
            "pricing_type": (self.ai_config.pricing_type if self.ai_config else "unknown"),
            "total_messages": self.total_messages,
            "total_cost_coins": float(self.total_cost_coins),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens_used": self.total_tokens_used,
            "total_characters_sent": self.total_characters_sent,
            "average_cost_per_message": (
                float(self.total_cost_coins) / self.total_messages if self.total_messages > 0 else 0
            ),
        }

    def mark_all_read(self):
        """علامت‌گذاری همه پیام‌ها به عنوان خوانده شده"""
        self.unread_messages = 0
        self.save(update_fields=["unread_messages"])
        self.messages.filter(is_read=False).update(is_read=True)

    @property
    def remaining_time_seconds(self):
        """محاسبه زمان باقیمانده به ثانیه"""
        from django.utils import timezone

        if not self.end_date:
            return 0

        now = timezone.now()
        if now > self.end_date:
            return 0

        delta = self.end_date - now
        return delta.total_seconds()

    @property
    def remaining_time_minutes(self):
        """محاسبه زمان باقیمانده به دقیقه"""
        return int(self.remaining_time_seconds / 60)
