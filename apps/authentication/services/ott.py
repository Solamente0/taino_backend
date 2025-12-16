import datetime

from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from base_utils.facades.cache import RedisCacheManager


class OTTGenerator(object):
    OTT_CACHE_KEY_TEMPLATE = getattr(settings, "OTT_TEMPLATE", "user-{user_identifier}-ott")

    def __init__(self, user_identifier: str, token=None, ttl=3600):
        self.user_identifier = user_identifier
        self.token = token if token is not None else self.gen_token(getattr(settings, "OTT_TOKEN_LENGTH", 20))
        self.key = self.ott_cache_key
        self.ttl = ttl
        self.cache = RedisCacheManager()
        super(OTTGenerator, self).__init__()

    @property
    def ott_cache_key(self) -> str:
        return self.OTT_CACHE_KEY_TEMPLATE.format(user_identifier=self.user_identifier)

    @staticmethod
    def gen_token(size=20):
        token = get_random_string(size)
        return token

    def set_ott_to_cache(self) -> int:
        random_code = self.token
        is_set = self.cache.set(self.ott_cache_key, str(random_code))
        self.cache.expire(
            self.ott_cache_key,
            datetime.datetime.now() + datetime.timedelta(minutes=self.ttl),
        )

        if not is_set:
            raise ValidationError(_("Unknown Error, please try again later"))

        return random_code

    def get_ott_from_cache(self) -> str:
        """
        GET OTT (ONE TIME TOKEN)
        """
        return self.cache.get(self.key)

    def verify_ott(self) -> bool:
        """
        VERIFY OTT (ONE TIME TOKEN)
        """
        return self.cache.validity(self.key, self.token)

    def invalidate_ott_in_cache(self) -> None:
        """
        DELETE OTT (ONE TIME TOKEN)
        """
        self.cache.delete(self.key)
