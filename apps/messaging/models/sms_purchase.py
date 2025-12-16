from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from apps.messaging.models.sms_balance import SMSBalance
from base_utils.base_models import TimeStampModel, CreatorModel, ActivableModel, AdminStatusModel

User = get_user_model()


class SMSPurchase(TimeStampModel, ActivableModel):
    """
    Model to track SMS purchase transactions
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sms_purchases")
    coins_spent = models.PositiveIntegerField(verbose_name=_("سکه های مصرف شده"))
    sms_quantity = models.PositiveIntegerField(verbose_name=_("تعداد پیامک"))
    purchase_date = models.DateTimeField(auto_now_add=True, verbose_name=_("تاریخ خرید"))

    class Meta:
        verbose_name = _("خرید پیامک")
        verbose_name_plural = _("خریدهای پیامک")

    def __str__(self):
        return f"{self.user} - {self.sms_quantity} پیامک"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Add purchased SMS to user's balance for new purchases
        if is_new:
            balance = SMSBalance.get_or_create_for_user(self.user)
            balance.add_balance(self.sms_quantity)
