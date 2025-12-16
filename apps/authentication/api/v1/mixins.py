import logging

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.authentication.services import UserService, OTTGenerator
from apps.country.services.query import CountryQuery
from base_utils.serializers.base import TainoBaseSerializer

log = logging.getLogger(__name__)


class CountryAlpha2Mixin(TainoBaseSerializer):
    country_alpha2 = serializers.CharField(
        required=False,
        allow_null=True,
        default="IR"
    )

    @staticmethod
    def validate_country_alpha2(value):
        """
        return country obj
        """
        if not value:
            return None

        country = CountryQuery.get_visible_countries().filter(code=value).first()
        if not country:
            raise serializers.ValidationError(_("Invalid or not active country code"))
        return country


class OTTMixin(TainoBaseSerializer):
    VALIDATE_BY_NUMBER = True
    token = serializers.CharField(
        required=True,
        max_length=20,
    )

    def validate_token(self, value):
        username = self.initial_data.get("username")
        if self.VALIDATE_BY_NUMBER:
            user_repository = UserService()
            country = self.validate_country_alpha2(self.initial_data.get("country_alpha2"))
            username = user_repository.concat_phone_number(username=username, country=country)

        token = OTTGenerator(username, value).verify_ott()
        if not token:
            log.info(f"user :{username}: entered token :{token}: not valid ")
            raise serializers.ValidationError(_("Invalid token"))

        return value


class UsernameFieldMixin(TainoBaseSerializer):
    RETURN_USER_OBJECT = False
    username = serializers.CharField()

    def validate_username(self, value):
        user_repository = UserService()
        username = user_repository.check_username(value)
        if username is not None:
            if self.RETURN_USER_OBJECT:
                country = self.validate_country_alpha2(self.initial_data.get("country_alpha2"))
                user = user_repository.get_and_validate_username(username=username, country=country)

                if user is not None:
                    return user
                else:
                    raise serializers.ValidationError(_("Invalid username or password"))
            else:
                return username

        # If it's neither an email nor a phone number, raise a validation error
        raise serializers.ValidationError(_("Username must be a valid email or phone number"))
