# Update in apps/wallet/models/transaction.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from base_utils.base_models import TimeStampModel, DescriptiveModel


class Transaction(TimeStampModel, DescriptiveModel):
    """
    Transactions model to track money and coin movements
    """

    TRANSACTION_TYPES = (
        ("deposit", "واریز ریال"),
        ("withdrawal", "برداشت ریال"),
        ("payment", "پرداخت"),
        ("refund", "بازگشت وجه"),
        ("consultation_fee", "هزینه مشاوره"),
        ("coin_purchase", "خرید سکه"),
        ("coin_usage", "استفاده از سکه"),
        ("coin_refund", "بازگشت سکه"),
        ("coin_reward", "جایزه سکه"),
        ("ai_chat", "گفتگوی هوش مصنوعی"),
        ("sms_buying", "خرید پیام کوتاه"),
        ("sms_usage", "استفاده از پیام کوتاه"),
    )

    TRANSACTION_STATUS = (
        ("pending", "در انتظار"),
        ("completed", "تکمیل شده"),
        ("failed", "ناموفق"),
        ("canceled", "لغو شده"),
    )

    wallet = models.ForeignKey("Wallet", on_delete=models.CASCADE, related_name="transactions", verbose_name="کیف پول")
    amount = models.DecimalField(default=0, max_digits=20, decimal_places=0, verbose_name="مبلغ", null=True, blank=True)
    coin_amount = models.DecimalField(
        max_digits=20, decimal_places=0, default=0, verbose_name="مقدار سکه", null=True, blank=True
    )
    sms_amount = models.DecimalField(
        max_digits=20, decimal_places=0, default=0, verbose_name="مقدار پیام کوتاه", null=True, blank=True
    )
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, verbose_name="نوع تراکنش")
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default="pending", verbose_name="وضعیت")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    reference_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="شماره پیگیری")
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, verbose_name="نرخ تبدیل")
    metadata = models.JSONField(null=True, blank=True, verbose_name="متادیتا")  # New field for additional data

    class Meta:
        verbose_name = "تراکنش"
        verbose_name_plural = "تراکنش‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        if self.coin_amount > 0:
            return f"{self.get_type_display()} - {self.amount} ریال - {self.coin_amount} سکه - {self.get_status_display()}"
        return f"{self.get_type_display()} - {self.amount} - {self.get_status_display()}"
