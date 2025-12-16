import logging
from typing import Any

from django.contrib.auth import get_user_model
from django_ratelimit.decorators import ratelimit

from apps.ratelimit.models import RateLimitConfig, RateLimitDefaultClass

User = get_user_model()
log = logging.getLogger(__name__)


def get_ratelimit_from_db(*, name: str) -> RateLimitConfig:
    try:
        RATELIMIT = RateLimitConfig.objects.get(name__iexact=name)
    except Exception as e:
        RATELIMIT = RateLimitConfig.objects.get(name="default")
    return RATELIMIT


def get_ratelimit(
    *, name: str, method: str = "POST", method_name: str = "post", block: bool = True, config: bool = False
) -> tuple[Any, str] | RateLimitConfig | RateLimitDefaultClass:
    try:
        RATELIMIT = get_ratelimit_from_db(name=name)
    except Exception as e:
        RATELIMIT = RateLimitDefaultClass(name=name, method=method, method_name=method_name)
    if config:
        return (
            ratelimit(key=RATELIMIT.key, rate=RATELIMIT.rate, method=RATELIMIT.method, group=RATELIMIT.group),
            RATELIMIT.method_name,
        )

    return RATELIMIT
