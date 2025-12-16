import logging
from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.services.auth import TainoAuthenticationBackend
from base_utils.serializers.base import TainoBaseSerializer

log = logging.getLogger(__name__)
User = get_user_model()


class AdminCustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "username"

    def validate(self, attrs: dict[str, Any]) -> dict[Any, Any]:
        try:
            auth_backend = TainoAuthenticationBackend(attrs["username"], attrs["password"])
            user = auth_backend.authenticate_credentials()
            tokens = auth_backend.get_user_tokens_data(user)
            return tokens
        except ValidationError as e:
            raise ValidationError(_("Invalid username or password"))
        except Exception as e:
            raise AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )


class AdminCustomTokenRefreshSerializer(TainoBaseSerializer):
    refresh = serializers.CharField()
    access = serializers.CharField(read_only=True)
    token_class = RefreshToken

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, str]:
        refresh = self.token_class(attrs["refresh"])

        data = {"access_token": str(refresh.access_token)}

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    # Attempt to blacklist the given refresh token
                    refresh.blacklist()
                except AttributeError:
                    # If blacklist app not installed, `blacklist` method will
                    # not be present
                    pass

            refresh.set_jti()
            refresh.set_exp()
            refresh.set_iat()

            data["refresh_token"] = str(refresh)
        return data


class AdminLogoutSerializer(TainoBaseSerializer):
    user_agent = serializers.CharField(max_length=1500, required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, str]:
        # TODO: implement logout logic
        return attrs
