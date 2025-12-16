from abc import abstractmethod

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from base_utils.validators import Validators
from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed

User = get_user_model()


class TainoAuthenticationBackend(ModelBackend):
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        super().__init__()

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if username is None or password is None:
            return
        try:
            user = User._default_manager.get(
                Q(phone_number__iexact=username) | Q(email__iexact=username) | Q(vekalat_id__exact=username)
            )
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            User().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user

    @classmethod
    def get_user_tokens_data(cls, user: User) -> dict:
        refresh = RefreshToken.for_user(user)
        return {
            "refresh_token": str(refresh),
            "access_token": str(refresh.access_token),
        }

    def authenticate_credentials(self) -> User:
        user = self._get_user()
        if not self.user_can_authenticate(user):
            raise ValidationError(_("You can not authenticate due to fact that your account is not active or blocked"))

        return user

    def _get_user(self) -> User:
        if self._is_identifier_email():
            user = User.objects.get(email=self.username)
        else:
            user = User.objects.get(phone_number=self.username)

        return user

    def _is_identifier_email(self) -> bool:
        return Validators.is_email(self.username)


class TainoThirdPartyAuthenticationBackend(TainoAuthenticationBackend):
    @abstractmethod
    def _get_user(self) -> User:
        raise NotImplementedError


class TainoGoogleAuthenticationBackend(TainoThirdPartyAuthenticationBackend):
    def __init__(self, email=None):
        self.email = email
        super().__init__()

    def _get_user(self) -> User:
        user = User.objects.get(email=self.email)
        return user


class NoExceptionJWTAuthentication(JWTAuthentication):
    """
    JWT Authentication that doesn't raise exceptions for missing/invalid tokens
    Returns None instead, allowing the view to handle unauthenticated requests
    """

    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except (InvalidToken, AuthenticationFailed):
            # Return None instead of raising an exception
            # This allows the view to handle unauthenticated requests
            return None
