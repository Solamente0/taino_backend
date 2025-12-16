import dataclasses

from django.conf import settings
from django.db import models

from base_utils.base_models import TimeStampModel, CreatorModel


@dataclasses.dataclass
class RateLimitDefaultClass:
    name: str
    group: str = None
    method: str = None
    method_name: str = None
    key: str = getattr(settings, "RATELIMIT_KEY", "user_or_ip")
    rate: str = getattr(settings, "RATELIMIT_RATE", "15/h")
    block: str = True


class RateLimitConfig(CreatorModel, TimeStampModel):
    name = models.CharField(max_length=20, unique=True, default=None)
    key = models.CharField(max_length=30, blank=True, null=True, default=None)
    rate = models.CharField(max_length=20, blank=True, null=True, default=None)
    group = models.CharField(max_length=10, blank=True, null=True, default=None)
    method = models.CharField(max_length=5, blank=True, null=True, default=None)
    method_name = models.CharField(max_length=20, blank=True, null=True, default=None)
    block = models.BooleanField(default=False)

    class Meta:
        verbose_name = "تنظیمات محدودیت درخواست"
        verbose_name_plural = "تنظیمات محدودیت درخواستها"
