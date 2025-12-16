import ast
import datetime
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError, NotFound

from apps.referral.models import ReferralLink, FlatReferral
from base_utils.facades.cache import RedisCacheManager
from base_utils.services import AbstractBaseService

log = logging.getLogger(__name__)
User = get_user_model()


class ReferralService(AbstractBaseService):
    REFERRAL_CACHE_KEY_TEMPLATE = getattr(settings, "REFERRAL_CACHE_KEY_TEMPLATE", "user-{referred}-invited")
    REFERRAL_CACHE_VALUE_TEMPLATE = getattr(settings, "REFERRAL_CACHE_VALUE", None)

    def __init__(self, token: str = None, referrer: User | str = None, referred: User | str = None, ttl: int = 3600 * 24):
        self.token = token
        self.referred = referred
        self.ttl = ttl
        self.cache = RedisCacheManager()

        if self.token is not None:
            self.referrer = referrer if referrer is not None else self.set_referrer()
        else:
            detail = self.get_referral_detail_from_cache()
            self.referrer = ast.literal_eval(detail)["referrer"]

        super(ReferralService, self).__init__()

    @staticmethod
    def get_username(user: User) -> str:
        try:
            return user.phone_number if user.phone_number is not None else user.email
        except Exception as e:
            return user

    def set_referrer(self):
        referral = self.get_referral_link()
        if referral:
            self.referrer = referral.user
            return referral.user
        else:
            raise NotFound(_("referral code not found"))

    @property
    def referral_cache_key(self) -> str:
        referred = self.get_username(self.referred)
        return self.REFERRAL_CACHE_KEY_TEMPLATE.format(referred=referred)

    @property
    def referral_cache_value(self) -> dict[str, str] | None:
        # self.referrer = self.set_referrer()
        self.REFERRAL_CACHE_VALUE_TEMPLATE = {
            "referrer": self.get_username(self.referrer),
            "referred": self.get_username(self.referred),
            "token": self.token,
        }
        return self.REFERRAL_CACHE_VALUE_TEMPLATE

    def set_referral_detail_to_cache(self) -> bool:
        is_set = self.cache.set(self.referral_cache_key, str(self.referral_cache_value))
        self.cache.expire(self.referral_cache_key, datetime.datetime.now() + datetime.timedelta(minutes=self.ttl))

        if not is_set:
            raise ValidationError(_("Unknown Error, please try again later"))

        return True

    def get_referral_detail_from_cache(self) -> str:
        """
        GET REFERRAL DETAIL
        """
        return self.cache.get(self.referral_cache_key)

    def invalidate_referral_detail_in_cache(self) -> None:
        """
        DELETE REFERRAL DETAIL
        """
        self.cache.delete(self.referral_cache_key)

    def get_referral_link(self) -> ReferralLink | None:
        try:
            return ReferralLink.objects.get(token=self.token)
        except Exception as e:
            raise ValidationError(_("referral token is invalid! please try again"))
            # return None

    def has_user_been_invited(self) -> bool | None:
        try:
            return FlatReferral.objects.filter(referred=self.referred).exists()
        except Exception as e:
            return None

    def check_referral_code(self):
        is_invited = self.has_user_been_invited()
        if is_invited:
            raise ValidationError(detail=_("You have already used an invitation code"))

        referral = self.get_referral_link()

        if not referral:
            raise NotFound(detail=_("Referral code not found"))

        self.referrer = referral.user

        if self.referred == self.referrer:
            raise ValidationError(detail=_("referrer and referred are the same"))
