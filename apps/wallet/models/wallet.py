# apps/wallet/models/wallet.py (Updated with coin support)
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, ActivableModel

User = get_user_model()


class Wallet(TimeStampModel, ActivableModel):
    """
    User's wallet model to handle financial transactions
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet", verbose_name=_("کاربر"))
    balance = models.DecimalField(max_digits=20, decimal_places=0, default=0, verbose_name=_("موجودی ریالی"))
    coin_balance = models.DecimalField(max_digits=20, decimal_places=0, default=0, verbose_name=_("موجودی سکه"))
    currency = models.CharField(max_length=3, default="IRR", verbose_name=_("واحد پولی"))

    class Meta:
        verbose_name = "کیف پول"
        verbose_name_plural = "کیف پول‌ها"

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.balance} {self.currency} - {self.coin_balance} سکه"
