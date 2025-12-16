# apps/ai_chat/models/chat_ai_config.py
import logging

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from base_utils.base_models import (
    TimeStampModel,
    ActivableModel,
    AdminStatusModel,
    CreatorModel,
    StaticalIdentifier,
)
from base_utils.numbers import safe_decimal_to_float

logger = logging.getLogger(__name__)


class AIStrengthEnum(models.TextChoices):
    MEDIUM = "medium", _("متوسط")
    STRONG = "strong", _("قوی")
    VERY_STRONG = "very_strong", _("خیلی قوی")
    SPECIAL = "special", _("ویژه")
    UNIQUE = "unique", _("یکتا")


class PricingTypeEnum(models.TextChoices):
    """نوع محاسبه قیمت"""

    MESSAGE_BASED = "message_based", _("ثابت به ازای هر پیام")
    ADVANCED_HYBRID = "advanced_hybrid", _("هیبریدی پیشرفته")


class ChatAIConfig(TimeStampModel, ActivableModel, AdminStatusModel, CreatorModel, StaticalIdentifier):
    """
    تنظیمات هوش مصنوعی با سیستم قیمت‌گذاری پیشرفته
    """

    # ═══════════════════════════════════════════════════════════
    # اطلاعات پایه
    # ═══════════════════════════════════════════════════════════
    general_config = models.ForeignKey(
        "GeneralChatAIConfig", on_delete=models.CASCADE, related_name="ai_configs", verbose_name=_("پیکربندی عمومی")
    )

    name = models.CharField(max_length=100, verbose_name=_("نام"))
    strength = models.CharField(
        max_length=20, default=AIStrengthEnum.MEDIUM, choices=AIStrengthEnum.choices, verbose_name=_("قدرت")
    )
    description = models.TextField(verbose_name=_("توضیحات"))

    # ═══════════════════════════════════════════════════════════
    # تنظیمات مدل
    # ═══════════════════════════════════════════════════════════
    model_name = models.CharField(max_length=100, default="deepseek-chat", verbose_name=_("نام مدل"))
    base_url = models.URLField(default=None, null=True, max_length=200, verbose_name="بیس یو آر ال")
    api_key = models.CharField(max_length=255, verbose_name=_("کلید API"))

    system_prompt = models.TextField(
        default="You are a legal assistant helping users with legal questions in Iran.",
        verbose_name=_("پرامپت سیستمی"),
        help_text=_("این پرامپت با دستورالعمل GeneralChatAIConfig ترکیب می‌شود"),
    )

    # ═══════════════════════════════════════════════════════════
    # پارامترهای پیش‌فرض
    # ═══════════════════════════════════════════════════════════
    default_temperature = models.FloatField(
        default=0.7, verbose_name=_("دمای پیش‌فرض"), help_text=_("مقدار پیشنهادی برای فرانت‌اند")
    )
    default_max_tokens = models.PositiveIntegerField(
        default=4000, verbose_name=_("حداکثر توکن پیش‌فرض"), help_text=_("مقدار پیشنهادی برای فرانت‌اند")
    )

    rate_limit_per_minute = models.PositiveIntegerField(default=10, verbose_name=_("محدودیت درخواست در دقیقه"))

    # ═══════════════════════════════════════════════════════════
    # نوع قیمت‌گذاری
    # ═══════════════════════════════════════════════════════════
    pricing_type = models.CharField(
        max_length=20,
        choices=PricingTypeEnum.choices,
        default=PricingTypeEnum.MESSAGE_BASED,
        verbose_name=_("نوع قیمت‌گذاری"),
        help_text=_("انتخاب روش محاسبه هزینه"),
    )

    # ═══════════════════════════════════════════════════════════
    # نوع اول: قیمت ثابت به ازای هر پیام
    # ═══════════════════════════════════════════════════════════
    cost_per_message = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name=_("هزینه هر پیام (سکه)"),
        help_text=_("فقط برای قیمت‌گذاری ثابت - هزینه ثابت برای هر پیام کاربر"),
    )

    # ═══════════════════════════════════════════════════════════
    # نوع دوم: قیمت هیبریدی پیشرفته
    # ═══════════════════════════════════════════════════════════

    # --- قیمت پایه ---
    hybrid_base_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name=_("هزینه پایه (سکه)"),
        help_text=_("هزینه ثابت اولیه برای هر درخواست (قیمت‌گذاری هیبریدی)"),
    )

    # --- بخش کاراکتر ---
    hybrid_char_per_coin = models.PositiveIntegerField(
        default=2500,
        validators=[MinValueValidator(1)],
        verbose_name=_("تعداد کاراکتر به ازای هر سکه"),
        help_text=_("مثال: 2500 کاراکتر = 1 سکه"),
    )

    hybrid_free_chars = models.PositiveIntegerField(
        default=5000,
        validators=[MinValueValidator(0)],
        verbose_name=_("کاراکترهای رایگان"),
        help_text=_("تعداد کاراکتری که رایگان است (مثلاً 5000 کاراکتر اول)"),
    )

    # --- بخش max_tokens (استپ) ---
    hybrid_tokens_min = models.PositiveIntegerField(
        default=1000,
        validators=[MinValueValidator(100)],
        verbose_name=_("حداقل توکن"),
        help_text=_("حداقل مقدار max_tokens قابل انتخاب"),
    )

    hybrid_tokens_max = models.PositiveIntegerField(
        default=8000,
        validators=[MinValueValidator(100)],
        verbose_name=_("حداکثر توکن"),
        help_text=_("حداکثر مقدار max_tokens قابل انتخاب"),
    )

    hybrid_tokens_step = models.PositiveIntegerField(
        default=500,
        validators=[MinValueValidator(1)],
        verbose_name=_("گام افزایش توکن (استپ)"),
        help_text=_("هر چند توکن یک استپ محسوب می‌شود؟ (مثلاً 500)"),
    )

    hybrid_cost_per_step = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name=_("هزینه هر استپ (سکه)"),
        help_text=_("هزینه به ازای هر استپ افزایش توکن"),
    )
    # ═══════════════════════════════════════════════════════════
    # قیمت‌گذاری بر اساس صفحه/عکس (برای attachment)
    # ═══════════════════════════════════════════════════════════
    free_pages = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("صفحات رایگان"),
        help_text=_("تعداد صفحات رایگان (مثلاً 5 صفحه اول رایگان)"),
    )

    cost_per_page = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name=_("هزینه هر صفحه/عکس (سکه)"),
        help_text=_("هزینه به ازای هر صفحه PDF یا هر تصویر"),
    )

    max_pages_per_request = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1)],
        verbose_name=_("حداکثر صفحه در هر درخواست"),
        help_text=_("محدودیت تعداد صفحات/تصاویر قابل ارسال"),
    )

    # ═══════════════════════════════════════════════════════════
    # قیمت‌گذاری بر اساس صوت (برای attachment)
    # ═══════════════════════════════════════════════════════════

    free_minutes = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("دقایق رایگان"),
        help_text=_("تعداد دقایق رایگان (مثلاً 5 دقیقه اول رایگان)"),
    )
    cost_per_minute = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name=_("هزینه هر دقیقه (سکه)"),
        help_text=_("هزینه به ازای هر دقیقه از صوت"),
    )
    max_minutes_per_request = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1)],
        verbose_name=_("حداکثر دقیقه در هر درخواست"),
        help_text=_("محدودیت دقیقه قابل ارسال"),
    )

    # ═══════════════════════════════════════════════════════════
    # تنظیمات نمایش
    # ═══════════════════════════════════════════════════════════
    is_default = models.BooleanField(default=False, verbose_name=_("پیش‌فرض"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("ترتیب نمایش"))

    related_service = models.ForeignKey(
        to="common.ServiceItem", verbose_name=_("سرویس مربوطه"), default=None, null=True, on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _("تنظیمات هوش مصنوعی")
        verbose_name_plural = _("تنظیمات هوش مصنوعی")
        ordering = ["general_config", "order", "strength"]
        unique_together = [["general_config", "strength"]]

    def __str__(self):
        return f"{self.general_config.name} - {self.get_strength_display()}"

    def save(self, *args, **kwargs):
        # اطمینان از اینکه فقط یک پیش‌فرض وجود داشته باشد
        if self.is_default:
            ChatAIConfig.objects.filter(general_config=self.general_config, is_default=True).exclude(pk=self.pk).update(
                is_default=False
            )
        super().save(*args, **kwargs)

    def get_combined_system_prompt(self):
        """ترکیب پرامپت سیستمی کلی با پرامپت اختصاصی"""
        general_instruction = self.general_config.system_instruction
        specific_prompt = self.system_prompt
        return f"{general_instruction}\n\n{specific_prompt}"

    # ═══════════════════════════════════════════════════════════
    # متدهای کمکی برای شناسایی نوع قیمت‌گذاری
    # ═══════════════════════════════════════════════════════════

    def is_message_based_pricing(self):
        """آیا این کانفیگ از قیمت‌گذاری ثابت استفاده می‌کند؟"""
        return self.pricing_type == PricingTypeEnum.MESSAGE_BASED

    def is_advanced_hybrid_pricing(self):
        """آیا این کانفیگ از قیمت‌گذاری هیبریدی پیشرفته استفاده می‌کند؟"""
        return self.pricing_type == PricingTypeEnum.ADVANCED_HYBRID

    # ═══════════════════════════════════════════════════════════
    # محاسبات قیمت
    # ═══════════════════════════════════════════════════════════

    def calculate_message_cost(self) -> dict:
        """
        محاسبه هزینه برای قیمت‌گذاری ثابت

        Returns:
            dict با اطلاعات هزینه
        """
        if not self.is_message_based_pricing():
            return {
                "cost": 0,
                "currency": "coins",
                "pricing_type": "not_message_based",
                "error": "این کانفیگ از قیمت‌گذاری ثابت استفاده نمی‌کند",
            }

        return {
            "cost": float(self.cost_per_message),
            "currency": "coins",
            "pricing_type": "message_based",
        }

    def calculate_advanced_hybrid_cost(self, character_count: int, max_tokens_requested: int) -> dict:
        """
        محاسبه هزینه برای قیمت‌گذاری هیبریدی پیشرفته

        Args:
            character_count: تعداد کاراکترهای ورودی کاربر
            max_tokens_requested: مقدار max_tokens درخواستی کاربر

        Returns:
            dict با جزئیات محاسبات هزینه
        """
        print(
            f"🚀 Starting advanced hybrid cost calculation - config_id={self.id}, config_name='{self.name}', character_count={character_count}, max_tokens_requested={max_tokens_requested}, pricing_type={self.pricing_type}",
            flush=True,
        )

        if not self.is_advanced_hybrid_pricing():
            print(
                f"⚠️ Invalid pricing type for advanced hybrid calculation - config_id={self.id}, expected_type={PricingTypeEnum.ADVANCED_HYBRID}, actual_type={self.pricing_type}",
                flush=True,
            )
            return {"pricing_type": "not_advanced_hybrid", "error": "این کانفیگ از قیمت‌گذاری هیبریدی پیشرفته استفاده نمی‌کند"}

        result = {
            "pricing_type": "advanced_hybrid",
            "character_count": character_count,
            "max_tokens_requested": max_tokens_requested,
            # هزینه پایه
            "base_cost": safe_decimal_to_float(self.hybrid_base_cost),
            # محاسبات کاراکتر
            "char_cost": 0,
            "free_chars_used": 0,
            "billable_chars": 0,
            # محاسبات استپ
            "step_cost": 0,
            "num_steps": 0,
            # جمع کل
            "total_cost": 0,
        }

        # ─────────────────────────────────────────────────────────
        # محاسبه هزینه بر اساس کاراکتر
        # ─────────────────────────────────────────────────────────
        print(
            f"📊 Calculating character-based cost - character_count={character_count}, hybrid_free_chars={self.hybrid_free_chars}, hybrid_char_per_coin={self.hybrid_char_per_coin}",
            flush=True,
        )

        if character_count > self.hybrid_free_chars:
            # کاراکترهای قابل محاسبه (بعد از رایگان)
            billable_chars = character_count - self.hybrid_free_chars
            result["billable_chars"] = billable_chars
            result["free_chars_used"] = self.hybrid_free_chars

            # محاسبه تعداد سکه‌های لازم
            # هر hybrid_char_per_coin کاراکتر = 1 سکه
            char_coins_needed = billable_chars / self.hybrid_char_per_coin
            import math

            char_cost_rounded = math.ceil(char_coins_needed)
            result["char_cost"] = float(char_cost_rounded)

            print(
                f"💳 Character cost calculated - billable_chars={billable_chars}, char_coins_needed={char_coins_needed:.2f}, char_cost_rounded={char_cost_rounded}, final_char_cost={result['char_cost']}",
                flush=True,
            )
        else:
            result["free_chars_used"] = character_count
            print(f"🆓 Character cost: Free tier applied - free_chars_used={character_count}", flush=True)

        # ─────────────────────────────────────────────────────────
        # محاسبه هزینه بر اساس استپ max_tokens
        # ─────────────────────────────────────────────────────────
        print(
            f"🔢 Calculating token step-based cost - original_max_tokens={max_tokens_requested}, hybrid_tokens_min={self.hybrid_tokens_min}, hybrid_tokens_max={self.hybrid_tokens_max}, hybrid_tokens_step={self.hybrid_tokens_step}, hybrid_cost_per_step={safe_decimal_to_float(self.hybrid_cost_per_step)}",
            flush=True,
        )

        # ابتدا بررسی محدوده
        original_tokens = max_tokens_requested
        if max_tokens_requested < self.hybrid_tokens_min:
            max_tokens_requested = self.hybrid_tokens_min
            print(
                f"📏 Max tokens adjusted to minimum - original={original_tokens}, adjusted={max_tokens_requested}", flush=True
            )
        elif max_tokens_requested > self.hybrid_tokens_max:
            max_tokens_requested = self.hybrid_tokens_max
            print(
                f"📏 Max tokens adjusted to maximum - original={original_tokens}, adjusted={max_tokens_requested}", flush=True
            )

        result["max_tokens_requested"] = max_tokens_requested

        # محاسبه تعداد استپ‌ها
        # فرمول: (max_tokens - min) / step
        tokens_above_min = max_tokens_requested - self.hybrid_tokens_min
        if tokens_above_min > 0:
            import math

            num_steps = math.ceil(tokens_above_min / self.hybrid_tokens_step)
            result["num_steps"] = num_steps
            result["step_cost"] = float(Decimal(str(num_steps)) * self.hybrid_cost_per_step)

            print(
                f"🎯 Step cost calculated - tokens_above_min={tokens_above_min}, num_steps={num_steps}, step_cost={result['step_cost']}",
                flush=True,
            )
        else:
            print(
                f"🎯 No step cost applied (at minimum tokens) - tokens_above_min={tokens_above_min}, step_cost=0", flush=True
            )

        # ─────────────────────────────────────────────────────────
        # محاسبه مجموع
        # ─────────────────────────────────────────────────────────
        result["total_cost"] = result["base_cost"] + result["char_cost"] + result["step_cost"]

        print(
            f"✅ Advanced hybrid cost calculation completed - config_id={self.id}, base_cost={result['base_cost']}, char_cost={result['char_cost']}, step_cost={result['step_cost']}, total_cost={result['total_cost']}",
            flush=True,
        )
        print(
            f"📋 Final breakdown - base: {result['base_cost']}, character: {result['char_cost']}, steps: {result['step_cost']}, total: {result['total_cost']}",
            flush=True,
        )

        return result

    def validate_max_tokens(self, max_tokens: int) -> tuple[bool, str, int]:
        """
        اعتبارسنجی مقدار max_tokens

        Args:
            max_tokens: مقدار درخواستی

        Returns:
            tuple: (valid, error_message, corrected_value)
        """
        if not self.is_advanced_hybrid_pricing():
            return True, "", max_tokens

        if max_tokens < self.hybrid_tokens_min:
            return (False, f"حداقل توکن مجاز {self.hybrid_tokens_min} است", self.hybrid_tokens_min)

        if max_tokens > self.hybrid_tokens_max:
            return (False, f"حداکثر توکن مجاز {self.hybrid_tokens_max} است", self.hybrid_tokens_max)

        return True, "", max_tokens

    def get_step_options(self) -> list:
        """
        دریافت لیست گزینه‌های استپ برای فرانت‌اند

        Returns:
            list: لیست دیکشنری‌های حاوی اطلاعات هر استپ
        """
        if not self.is_advanced_hybrid_pricing():
            return []

        options = []
        current = self.hybrid_tokens_min

        while current <= self.hybrid_tokens_max:
            # محاسبه تعداد استپ
            tokens_above_min = current - self.hybrid_tokens_min
            import math

            num_steps = math.ceil(tokens_above_min / self.hybrid_tokens_step) if tokens_above_min > 0 else 0

            # FIX: Ctainoert Decimal to float before multiplication
            step_cost = safe_decimal_to_float(self.hybrid_cost_per_step) * num_steps

            options.append(
                {
                    "value": current,
                    "label": f"{current} توکن",
                    "steps": num_steps,
                    "step_cost": step_cost,
                }
            )

            current += self.hybrid_tokens_step

        return options
