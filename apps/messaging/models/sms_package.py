# apps/messaging/models/sms_package.py
from django.db import models
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, ActivableModel


class SMSPackage(TimeStampModel, ActivableModel):
    """
    Model for predefined SMS packages that users can purchase
    """

    value = models.PositiveIntegerField(verbose_name=_("تعداد پیامک"))
    label = models.CharField(max_length=50, verbose_name=_("برچسب نمایشی"))
    coin_cost = models.PositiveIntegerField(verbose_name=_("هزینه به سکه"))
    order = models.PositiveSmallIntegerField(default=0, verbose_name=_("ترتیب نمایش"))
    description = models.TextField(blank=True, null=True, default=None, verbose_name=_("توضیحات"))

    class Meta:
        verbose_name = _("بسته پیامک")
        verbose_name_plural = _("بسته های پیامک")
        ordering = ["order", "value"]

    def __str__(self):
        return f"{self.label} ({self.value} پیامک)"
