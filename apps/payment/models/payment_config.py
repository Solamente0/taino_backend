# apps/payment/models/payment_config.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, ActivableModel


class ZarinpalPaymentConfig(TimeStampModel, ActivableModel):
    """
    Configuration model for Zarinpal payment gateway

    This model stores merchant ID, API key, and other gateway settings
    with ability to toggle between sandbox and production modes.
    """

    merchant_id = models.CharField(max_length=100, verbose_name=_("شناسه پذیرنده"))
    api_key = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("کلید API"))
    is_sandbox = models.BooleanField(default=True, verbose_name=_("محیط تست"))
    description = models.TextField(blank=True, null=True, verbose_name=_("توضیحات"))
    is_default = models.BooleanField(default=False, verbose_name=_("پیش‌فرض"))

    class Meta:
        verbose_name = _("تنظیمات درگاه زرین‌پال")
        verbose_name_plural = _("تنظیمات درگاه زرین‌پال")
        ordering = ["-created_at"]

    def __str__(self):
        mode = "Sandbox" if self.is_sandbox else "Production"
        return f"Zarinpal Config - {mode} - {self.merchant_id}"

    def save(self, *args, **kwargs):
        # If this is marked as default, unmark all others
        if self.is_default:
            ZarinpalPaymentConfig.objects.filter(is_default=True).update(is_default=False)

        # If no default exists, make this the default
        elif not ZarinpalPaymentConfig.objects.filter(is_default=True).exists():
            self.is_default = True

        super().save(*args, **kwargs)

    @classmethod
    def get_default(cls):
        """Get the default Zarinpal settings"""
        default = cls.objects.filter(is_default=True, is_active=True).first()
        if not default:
            # If no default exists, get the most recent active settings
            default = cls.objects.filter(is_active=True).order_by("-created_at").first()
            if default:
                default.is_default = True
                default.save()
        return default

    @classmethod
    def get_merchant_id(cls):
        """Get merchant ID from database or settings"""
        default = cls.get_default()
        if default:
            return default.merchant_id
        return settings.ZARINPAL_MERCHANT_ID

    @classmethod
    def get_is_sandbox(cls):
        """Get sandbox mode from database or settings"""
        default = cls.get_default()
        if default:
            return default.is_sandbox
        return settings.ZARINPAL_SANDBOX

    @classmethod
    def get_api_key(cls):
        """Get API key from database"""
        default = cls.get_default()
        if default:
            return default.api_key
        return None
