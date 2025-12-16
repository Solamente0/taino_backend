import datetime
import logging
import random
from typing import Any

import pyotp
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.authentication.services.generators import GenerateKey
from apps.messaging.services.templates import TainoEmailTemplate
from apps.messaging.tasks import send_email_task, send_verification_sms_task
from base_utils.facades.cache import RedisCacheManager
from base_utils.validators import Validators

log = logging.getLogger(__name__)


class OTPGenerator:
    OTP_CACHE_KEY_TEMPLATE = getattr(settings, "OTP_TEMPLATE", "user-{user_identifier}-otp")
    # Debug mode constant OTP
    DEBUG_OTP = "123456"

    def __init__(
            self,
            user_identifier: str,
            country: "Country" = None,
            interval: int | None = None,
            otp: str | None = None,
            language_code: str | None = None,
            template_code: str | None = None,
    ):
        self.user_identifier = user_identifier
        self.key = self.otp_cache_key
        self.interval = interval or getattr(settings, "DEFAULT_OTP_EXPIRE_TIME", 120)
        self.otp = otp
        self.country = country
        self.language_code = language_code
        self.template_code = template_code
        self.cache = RedisCacheManager()

    def get_template_info(self, code: str) -> dict[str, Any]:
        result = {
            "template_code": self.template_code,
            "language_code": self.language_code,
            "context": {"code": code},
        }
        if "user_fullname" in TainoEmailTemplate.CONTEXT_MAP[self.template_code]:
            result["context"]["user_fullname"] = self.user_identifier
        log.info(f"context_result: {result}")
        print(f"context_result: {result}")
        return result

    @property
    def otp_cache_key(self) -> str:
        return self.OTP_CACHE_KEY_TEMPLATE.format(user_identifier=self.user_identifier)

    def set_otp_to_cache(self) -> int:
        # Use constant OTP in debug mode
        if settings.DEBUG:
            random_code = self.DEBUG_OTP
            log.info(f"🔧 DEBUG MODE: Using constant OTP: {random_code} for {self.user_identifier}")
        else:
            random_code = self._generate_random_number_with_size(getattr(settings, "DEFAULT_OTP_LENGTH"))

        is_set = self.cache.set(self.otp_cache_key, str(random_code))
        self.cache.expire(
            self.otp_cache_key,
            datetime.datetime.now() + datetime.timedelta(seconds=self.interval),
            )

        if not is_set:
            raise ValidationError(_("Error in sending OTP code, please try again later"))

        return random_code

    def get_otp_from_cache(self) -> str:
        return self.cache.get(self.otp_cache_key)

    def get_otp_remaining_time(self) -> int:
        return self.cache.ttl(self.otp_cache_key)

    def verify_otp(self):
        return self.cache.validity(self.otp_cache_key, self.otp)

    def invalidate_otp_in_cache(self):
        self.cache.delete(self.otp_cache_key)

    def _generate_random_number_with_size(self, number_of_digits: int = 6) -> int:
        lower = 10 ** (number_of_digits - 1)
        upper = 10**number_of_digits - 1
        return random.randint(lower, upper)

    def generate_totp(self) -> tuple[str, float]:
        b64_key = GenerateKey().get_b74_key(key=self.key)
        totp = pyotp.TOTP(b64_key, interval=self.interval)
        time_remaining = totp.interval - datetime.datetime.now().timestamp() % totp.interval
        return totp.now().strip(), time_remaining  # => '492039'

    def verify_totp(self) -> bool:
        b64_key = GenerateKey().get_b74_key(key=self.key)
        totp = pyotp.TOTP(b64_key, interval=self.interval)
        return totp.verify(self.otp)

    def send_code(self):
        from apps.messaging.services.templates import TainoDefaultMessageFormats

        previous_code = self.get_otp_from_cache()
        otp_remaining = self.get_otp_remaining_time()

        if previous_code and otp_remaining > 30:
            return False, otp_remaining

        code = self.set_otp_to_cache()
        otp_remaining = self.get_otp_remaining_time()

        log.info(f"{code=}")

        # Skip actual sending in debug mode
        if settings.DEBUG:
            log.info(f"🔧 DEBUG MODE: Skipping OTP send. Use OTP: {code} for {self.user_identifier}")
            print(f"🔧 DEBUG MODE: OTP for {self.user_identifier} is: {code}", flush=True)
            return True, otp_remaining

        # Only send actual messages in production
        if Validators.is_email(self.user_identifier):
            send_email_task.delay(
                subject=TainoDefaultMessageFormats.EMAIL_VERIFICATION_SUBJECT.value,
                to=self.user_identifier,
                context=self.get_template_info(str(code)),
            )
        else:
            send_verification_sms_task.delay(
                dial_code=self.country.dial_code if self.country is not None else None,
                code=code,
                mobile_number=self.user_identifier,
            )

        return True, otp_remaining
