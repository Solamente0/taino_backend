from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, CreatorModel, ActivableModel, AdminStatusModel

User = get_user_model()


class SMSBalance(TimeStampModel, ActivableModel):
    """
    Model to track user's SMS balance
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="sms_balance")
    balance = models.PositiveIntegerField(default=0, verbose_name=_("تعداد پیامک باقیمانده"))

    class Meta:
        verbose_name = _("موجودی پیامک")
        verbose_name_plural = _("موجودی های پیامک")

    def __str__(self):
        return f"{self.user} - {self.balance}"

    def add_balance(self, amount):
        """Add SMS credits to user's balance"""
        self.balance += amount
        self.save()

    def deduct_balance(self, amount=1):
        """
        Deduct SMS credits from user's balance
        Returns True if successful, False if insufficient balance
        """
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            return True
        return False

    @classmethod
    def get_or_create_for_user(cls, user):
        """Get or create SMS balance for a user"""
        balance, created = cls.objects.get_or_create(user=user)
        return balance
