# apps/wallet/models/coin_package.py
from django.db import models
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, ActivableModel


class CoinPackage(TimeStampModel, ActivableModel):
    """
    Model for predefined coin packages that users can purchase
    Each package has its own price and can be role-specific
    """

    value = models.PositiveIntegerField(verbose_name=_("تعداد سکه"))
    label = models.CharField(max_length=50, verbose_name=_("برچسب نمایشی"))
    price = models.DecimalField(
        max_digits=12, decimal_places=0, default=0, verbose_name=_("قیمت به ریال"), help_text=_("قیمت واقعی این پکیج به ریال")
    )
    order = models.PositiveSmallIntegerField(default=0, verbose_name=_("ترتیب نمایش"))
    description = models.TextField(blank=True, null=True, default=None, verbose_name=_("توضیحات"))

    # New field for role-based packages
    role = models.ForeignKey(
        to="authentication.UserType",
        on_delete=models.CASCADE,
        related_name="coin_packages",
        null=True,
        blank=True,
        verbose_name=_("نقش کاربری"),
        help_text=_("اگر مشخص شود، فقط برای این نقش نمایش داده می‌شود. اگر خالی باشد، برای همه نمایش داده می‌شود"),
    )

    class Meta:
        verbose_name = _("بسته سکه")
        verbose_name_plural = _("بسته های سکه")
        ordering = ["order", "value"]

    def __str__(self):
        role_name = f" - {self.role.name}" if self.role else ""
        return f"{self.label} ({self.value} سکه - {self.price} ریال){role_name}"

    @property
    def price_per_coin(self):
        """Calculate price per coin for this package"""
        if self.value > 0:
            return self.price / self.value
        return 0

    @classmethod
    def get_packages_for_user(cls, user):
        """
        Get available packages for a specific user based on their role
        Returns packages specific to user's role or generic packages
        """
        if not user or not hasattr(user, "role") or not user.role:
            # Return only generic packages (no role specified)
            return cls.objects.filter(is_active=True, role__isnull=True).order_by("order", "value")

        # Return packages for user's role OR generic packages
        from django.db.models import Q

        return cls.objects.filter(Q(role=user.role) | Q(role__isnull=True), is_active=True).order_by("order", "value")
