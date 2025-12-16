import logging
from typing import Any, Dict

from django.conf import settings
from django.contrib.auth import password_validation, get_user_model
from django.utils.translation import gettext_lazy as _, get_language_from_request
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import PasswordField
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.api.v1.mixins import CountryAlpha2Mixin, OTTMixin, UsernameFieldMixin
from apps.authentication.exceptions import InvalidUsernameOrPassword, Required
from apps.authentication.services import OTTGenerator, OTPGenerator
from apps.authentication.services import UserService
from apps.authentication.services.auth import TainoAuthenticationBackend, TainoGoogleAuthenticationBackend
from apps.authentication.services.query import UserQuery
from apps.referral.services import ReferralService
from apps.user.api.v1.serializers import OutputUserProfileModelSerializer  # todo fix impoort
from base_utils.serializers.base import TainoBaseSerializer, TainoBaseModelSerializer
from base_utils.validators import Validators

log = logging.getLogger(__name__)
User = get_user_model()


class CustomTokenObtainPairSerializer(TainoBaseSerializer):
    username = serializers.CharField(write_only=True, required=True)
    password = PasswordField(required=True)
    default_error_messages = {"no_active_account": _("No active account found with the given credentials")}

    def validate(self, attrs: dict[str, Any]) -> dict[Any, Any]:
        try:
            auth_backend = TainoAuthenticationBackend(attrs["username"], attrs["password"])
            user = auth_backend.authenticate_credentials()
            tokens = auth_backend.get_user_tokens_data(user)
            return tokens
        except ValidationError as e:
            raise e
        except Exception as e:
            raise AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )


class OutputSendOTPSerializer(TainoBaseSerializer):
    message = serializers.CharField()
    otp_time_remaining = serializers.IntegerField(default=None, required=False)
    debug_otp = serializers.CharField(default=None, required=False, allow_null=True)


class OutputVerifyOTPSerializer(TainoBaseSerializer):
    message = serializers.CharField()
    token = serializers.CharField(default=None, required=False)


class OutputCredentialSerializer(TainoBaseSerializer):
    refresh_token = serializers.CharField()
    access_token = serializers.CharField()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    @property
    def data(self):
        user = self.user
        request = self.context["request"]
        credentials = self.context["credentials"]

        if user is None:
            raise serializers.ValidationError(_("No such user with the given credentials"))

        data = TainoAuthenticationBackend()
        data.authenticate(request, user.username, credentials["password"])
        serialized_data = data.get_user_tokens_data(user)

        return serialized_data


class SendOTPSerializer(UsernameFieldMixin, CountryAlpha2Mixin):
    def validate(self, attrs):
        country = attrs.get("country_alpha2", None)
        user_repository = UserService()
        username = user_repository.check_and_repair_username(username=attrs["username"], country=country)
        log.info(f"username::: {username}")
        attrs["username"] = username
        attrs["country_object"] = country
        return attrs

    def to_representation(self, instance):
        username = self.validated_data.get("username")
        country_object = self.validated_data.pop("country_object", None)
        language_code = self.context["request"].META.get("HTTP_ACCEPT_LANGUAGE", "en")
        otp_generator = OTPGenerator(
            user_identifier=username, country=country_object, language_code=language_code, template_code="otp.html"
        )
        is_sent, time_remaining = otp_generator.send_code()
        return OutputSendOTPSerializer(
            {"message": _("Your authentication code has been sent"), "otp_time_remaining": time_remaining}
        ).data

class SendForgotPasswordOTPSerializer(SendOTPSerializer):
    def validate(self, attrs):
        country = attrs.get("country_alpha2", None)
        user_repository = UserService()
        username = user_repository.check_and_repair_username(username=attrs["username"], country=country)

        if not user_repository.get_user_by_username(username):
            raise NotFound(_("No such user, please enter a valid email or phone number"))

        attrs["username"] = username
        attrs["country_object"] = country
        return attrs

    def to_representation(self, instance):
        from django.conf import settings

        username = self.validated_data.get("username")
        country_object = self.validated_data.pop("country_object", None)

        otp_generator = OTPGenerator(
            user_identifier=username,
            country=country_object,
            template_code="reset-password.html",
        )
        is_sent, time_remaining = otp_generator.send_code()

        response_data = {
            "message": _("Your authentication code has been sent"),
            "otp_time_remaining": time_remaining
        }

        # Include OTP in response when in DEBUG mode
        if settings.DEBUG:
            debug_otp = otp_generator.get_otp_from_cache()
            response_data["debug_otp"] = debug_otp
            log.info(f"🔧 DEBUG MODE: Including OTP in response: {debug_otp}")

        return OutputSendOTPSerializer(response_data).data

class SendRegistrationCodeSerializer(SendOTPSerializer):
    referral_code = serializers.CharField(
        default=None,
        required=False,
        max_length=10,
    )

    def validate_referral_code(self, value):
        if value == "" or value is None:
            return None

        validated_data = self.validate(self.initial_data)
        username = validated_data.get("username")
        country = self.validate_country_alpha2(validated_data.get("country_alpha2"))

        user_repo = UserService()
        username = user_repo.check_and_repair_username(username, country)

        return value

    def to_representation(self, instance):
        from django.conf import settings

        username = self.validated_data.get("username")
        country_object = self.validated_data.pop("country_object", None)

        user_repository = UserService()
        username = user_repository.check_and_repair_username(username=username, country=country_object)

        if user_repository.get_user_by_username(username):
            raise ValidationError(_("User already exists! Please Login"))

        otp_generator = OTPGenerator(
            user_identifier=username,
            country=country_object,
            language_code="fa",
            template_code="registration.html"
        )
        is_sent, time_remaining = otp_generator.send_code()

        response_data = {
            "message": _("Your authentication code has been sent"),
            "otp_time_remaining": time_remaining
        }

        # Include OTP in response when in DEBUG mode
        if settings.DEBUG:
            debug_otp = otp_generator.get_otp_from_cache()
            response_data["debug_otp"] = debug_otp
            log.info(f"🔧 DEBUG MODE: Including OTP in response: {debug_otp}")

        return OutputSendOTPSerializer(response_data).data



class VerifyOTPSerializer(UsernameFieldMixin, CountryAlpha2Mixin):
    RETURN_USER_OBJECT = False
    otp = serializers.CharField()

    def validate(self, attrs):
        country = attrs.get("country_alpha2", None)
        user_repository = UserService()
        username = user_repository.check_and_repair_username(username=attrs["username"], country=country)
        otp_generator = OTPGenerator(user_identifier=username, otp=attrs["otp"])
        if not otp_generator.verify_otp():
            raise ValidationError(_("Invalid authentication code. Please double-check the code you entered and try again"))
        # otp_generator.invalidate_otp_in_cache()
        attrs["username"] = username
        return attrs

    def to_representation(self, instance):
        username = self.validated_data.get("username")
        token = OTTGenerator(user_identifier=username)
        token.set_ott_to_cache()
        output = OutputVerifyOTPSerializer({"message": _("OTP Verified"), "token": token.get_ott_from_cache()}).data

        return output


# Update the RegisterSerializer in apps/authentication/api/v1/serializers.py


class RegisterSerializer(UsernameFieldMixin, CountryAlpha2Mixin, OTTMixin):
    password = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    passwordless = serializers.BooleanField(required=False, default=False)

    first_name = serializers.CharField()
    last_name = serializers.CharField()
    national_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    default_country_code = serializers.CharField(required=False, allow_null=True, default="IR")
    role = serializers.CharField(required=False, allow_null=True)

    @staticmethod
    def validate_national_code(value):
        if not value or value.strip() == "":
            return None

        # Check uniqueness
        if User.objects.filter(national_code=value).exists():
            raise serializers.ValidationError(_("User with this National Code exists!"))
        return value

    def validate(self, attrs):
        passwordless = attrs.get("passwordless", False)
        password = attrs.get("password")

        # If not passwordless, password is required
        if not passwordless and not password:
            raise ValidationError({"password": _("Password is required when passwordless is False or not specified")})

        # If passwordless is True, password should not be provided
        if passwordless and password:
            raise ValidationError({"passwordless": _("Cannot set both passwordless=True and provide a password")})

        return attrs

    def create(self, validated_data):
        username = validated_data.get("username")
        phone_country = validated_data.pop("country_alpha2", None)
        default_country_code = validated_data.pop("default_country_code", None)
        default_role = validated_data.pop("role", None)
        token = validated_data.pop("token", None)
        passwordless = validated_data.pop("passwordless", False)

        user_repository = UserService()
        user = user_repository.get_and_validate_username(username, phone_country)

        if user:
            raise ValidationError(_("User already exists! Please login instead"))

        validated_data["username"] = user_repository.check_and_repair_username(username, phone_country)

        phone_country_code = phone_country.code if phone_country else None

        # Handle password - either set it or make it unusable
        password = validated_data.pop("password", None)

        user = user_repository.create_user_with_username(
            phone_country=phone_country_code,
            role_static_name=default_role,
            password=password,
            is_passwordless=passwordless,
            **validated_data,
        )

        if user is None:
            raise ValidationError(_("Username must be a valid email or phone number"))

        user_repository.set_user_phone_country(user=user, country=phone_country)
        user_repository.set_user_default_country(user=user, country_code=default_country_code)
        user_repository.set_user_role(user=user, role_static_name=default_role)

        username = user_repository.check_and_repair_username(username, phone_country)
        user_repository.do_referral(referred=username)

        OTTGenerator(username).invalidate_ott_in_cache()

        # Check if this user matches any existing client records
        from apps.lawyer_office.services.client import ClientService

        matching_clients = ClientService.find_matching_clients(email=user.email, phone_number=user.phone_number)

        if matching_clients.exists():
            for client in matching_clients:
                ClientService.connect_user_to_client(user, client)

        return user

    def to_representation(self, instance):
        username = self.validated_data.get("username")
        passwordless = self.initial_data.get("passwordless", False)

        user_repository = UserService()
        user = user_repository.get_user_by_username(username=username)

        # If passwordless registration, generate tokens without password
        if passwordless:
            auth_backend = TainoAuthenticationBackend()
            tokens = auth_backend.get_user_tokens_data(user)
            return tokens
        else:
            # Regular registration with password
            credentials = {"username": username, "password": self.initial_data.get("password")}
            output = OutputCredentialSerializer(
                user=user, context={"request": self.context.get("request"), "credentials": credentials}
            ).data
            return output


class LoginSerializer(UsernameFieldMixin, CountryAlpha2Mixin):
    RETURN_USER_OBJECT = True
    password = serializers.CharField(write_only=True, required=True)
    lang_code = serializers.CharField(required=False, allow_null=True, default="en")

    def validate(self, attrs):
        user = attrs["username"]
        # lang_code = attrs.get("lang_code", "en")

        if not user.check_password(attrs["password"]):
            raise InvalidUsernameOrPassword()
        # if lang_code:
        #     language = Language.objects.filter(code__iexact=lang_code)
        #     if language.exists():
        #         user.language = language.first()
        #         user.save()
        attrs["user"] = user
        return attrs

    def to_representation(self, instance):
        user = self.validated_data.get("user")
        credentials = {"username": user.username, "password": self.validated_data.get("password")}
        output = OutputCredentialSerializer(
            user=user, context={"request": self.context["request"], "credentials": credentials}
        ).data
        return output


class SetEmailSerializer(OTTMixin):
    VALIDATE_BY_NUMBER = False
    username = serializers.EmailField()

    @staticmethod
    def validate_username(value):
        if Validators.is_email(value):
            user = UserQuery.get_user_by_email(email=value)
            if user:
                raise ValidationError(_("This Email is Already Taken"))
            return value
        else:
            raise ValidationError(_("Please enter a valid email address"))

    def update(self, instance, validated_data):
        email = validated_data.get("username", instance.email)
        instance.email = email
        instance.save()
        return instance

    def to_representation(self, instance):
        return OutputUserProfileModelSerializer(instance=instance, context=self.context).data


class SetNumberSerializer(UsernameFieldMixin, CountryAlpha2Mixin, OTTMixin):
    VALIDATE_BY_NUMBER = True
    username = serializers.CharField()

    def update(self, instance, validated_data):
        if instance.phone_number is not None:
            raise ValidationError(_("You already have a phone number"))

        instance.phone_number = validated_data.get("username", instance.phone_number)
        instance.save()

        username = validated_data.get("username")
        token = validated_data.get("token")

        OTTGenerator(username, token).invalidate_ott_in_cache()
        return instance


class ForgotPasswordSerializer(UsernameFieldMixin, CountryAlpha2Mixin, OTTMixin):
    RETURN_USER_OBJECT = False
    new_password = serializers.CharField()
    new_password_confirm = serializers.CharField()

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        username = self.initial_data.get("username")
        new_password = validated_data.get("new_password")
        new_password_confirm = validated_data.get("new_password_confirm")
        if username is None:
            raise ValidationError(_("Please enter a valid email or phone number"))
        user_repository = UserService()
        username = user_repository.check_username(username)
        if username is None:
            raise serializers.ValidationError(_("Username must be a valid email or phone number"))

        if new_password != new_password_confirm:
            raise ValidationError(_("Passwords are not match"))

        password_validation.validate_password(
            new_password_confirm,
            # user
        )
        return validated_data

    def update(self, instance, validated_data):
        username = validated_data.get("username")
        token = validated_data.pop("token", None)
        country = validated_data.pop("country_alpha2", None)
        log.info(f"username in forgot password: {username}")
        user_repository = UserService()

        user = user_repository.get_and_validate_username(username=username, country=country)
        log.info(f"user in forgot password: {user}")

        if user is None:
            raise serializers.ValidationError(_("No such user with the given credentials"))

        new_password = validated_data.get("new_password")
        user.set_password(new_password)
        user.save()
        username = user_repository.check_and_repair_username(username=username, country=country)
        OTTGenerator(username, token).invalidate_ott_in_cache()
        return user


class ChangePasswordSerializer(TainoBaseSerializer):
    new_password = serializers.CharField()
    new_password_confirm = serializers.CharField()
    old_password = serializers.CharField(required=False)

    # user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        user = self.context["request"].user
        old_password = validated_data.get("old_password")
        new_password = validated_data.get("new_password")
        new_password_confirm = validated_data.get("new_password_confirm")

        if user.has_usable_password() and not old_password:
            raise Required(field="old_password")
        if not user.check_password(old_password):
            raise ValidationError(_("Your previous password is incorrect"))
        if new_password != new_password_confirm:
            raise ValidationError(_("Passwords are not match"))
        password_validation.validate_password(new_password_confirm, user)
        return validated_data

    def update(self, instance, validated_data):
        instance.set_password(validated_data.get("new_password"))
        instance.save()
        return instance


class SetUserPasswordSerializer(TainoBaseSerializer):
    new_password = serializers.CharField()
    new_password_confirm = serializers.CharField()

    # user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        user = self.context["request"].user
        new_password = validated_data.get("new_password")
        new_password_confirm = validated_data.get("new_password_confirm")

        if user.has_usable_password():
            raise ValidationError(_("You already have a password, please change it"))
        if new_password != new_password_confirm:
            raise ValidationError(_("Passwords are not match"))
        password_validation.validate_password(new_password_confirm, user)
        return validated_data

    def update(self, instance, validated_data):
        instance.set_password(validated_data.get("new_password"))
        return instance


class HasPasswordSerializer(TainoBaseSerializer):
    has_password = serializers.BooleanField()


class UserProfileModelSerializer(TainoBaseModelSerializer):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "avatar",
            "country",
        )

    def validate(self, attrs):
        instance = getattr(self, "instance", None)
        attrs = super().validate(attrs)

        if ("state" in attrs and "country" in attrs) and (
            attrs.get("state").country.code.lower() != attrs.get("country").code.lower()
        ):
            raise ValidationError(_("Country and State do not match"))

        if ("state" in attrs and "city") and (attrs.get("state") != attrs.get("city").state):
            raise ValidationError(_("State and City do not match"))

        return attrs


class OutputMessageSerializer(TainoBaseSerializer):
    message = serializers.CharField()


class CustomTokenRefreshSerializer(TainoBaseSerializer):
    refresh_token = serializers.CharField()
    access_token = serializers.CharField(read_only=True)
    token_class = RefreshToken

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, str]:
        refresh_token = self.token_class(attrs["refresh_token"])

        data = {"access_token": str(refresh_token.access_token)}

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    # Attempt to blacklist the given refresh token
                    refresh_token.blacklist()
                except AttributeError:
                    # If blacklist app not installed, `blacklist` method will
                    # not be present
                    pass

            refresh_token.set_jti()
            refresh_token.set_exp()
            refresh_token.set_iat()

            data["refresh_token"] = str(refresh_token)
        return data


class LogoutSerializer(TainoBaseSerializer):
    user_agent = serializers.CharField(max_length=1500, required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, str]:
        # TODO: implement logout logic

        try:
            if self.context["request"].user:

                from apps.notification.models import UserNotificationToken

                UserNotificationToken.objects.filter(
                    user=self.context["request"].user, user_agent=attrs.get("user_agent", None)
                ).delete()

        except Exception as e:
            pass

        return attrs


class MobileCustomTokenObtainPairSerializer(TainoBaseSerializer):
    username_field = "username"

    def validate(self, attrs: dict[str, Any]) -> dict[Any, Any]:
        try:
            auth_backend = TainoGoogleAuthenticationBackend(attrs["username"])
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


class CheckUserExistsSerializer(UsernameFieldMixin, CountryAlpha2Mixin):
    """
    Serializer to check if a user exists by username (email or phone number)
    """

    RETURN_USER_OBJECT = False

    def validate(self, attrs):
        country = attrs.get("country_alpha2", None)
        user_repository = UserService()
        username = user_repository.check_and_repair_username(username=attrs["username"], country=country)

        # Check if user exists
        user_exists = user_repository.get_user_by_username(username=username) is not None

        attrs["username"] = username
        attrs["user_exists"] = user_exists
        return attrs

    def to_representation(self, instance):
        return {"exists": self.validated_data.get("user_exists", False)}


class OutputUserExistsSerializer(TainoBaseSerializer):
    """
    Output serializer for user exists check
    """

    exists = serializers.BooleanField()


class SendLoginOTPSerializer(UsernameFieldMixin, CountryAlpha2Mixin):
    """
    Serializer for sending OTP for login purposes
    User must already exist
    """

    def validate(self, attrs):
        country = attrs.get("country_alpha2", None)
        user_repository = UserService()
        username = user_repository.check_and_repair_username(username=attrs["username"], country=country)

        # Check if user exists
        user = user_repository.get_user_by_username(username)
        if not user:
            raise NotFound(_("No account found with this email or phone number. Please register first."))

        log.info(f"Sending login OTP to username: {username}")
        attrs["username"] = username
        attrs["country_object"] = country
        return attrs

    def to_representation(self, instance):
        from django.conf import settings

        username = self.validated_data.get("username")
        country_object = self.validated_data.pop("country_object", None)
        language_code = self.context["request"].META.get("HTTP_ACCEPT_LANGUAGE", "en")

        otp_generator = OTPGenerator(
            user_identifier=username,
            country=country_object,
            language_code=language_code,
            template_code="otp-login.html"
        )
        is_sent, time_remaining = otp_generator.send_code()

        response_data = {
            "message": _("Login code has been sent to your email/phone"),
            "otp_time_remaining": time_remaining
        }

        # Include OTP in response when in DEBUG mode
        if settings.DEBUG:
            debug_otp = otp_generator.get_otp_from_cache()
            response_data["debug_otp"] = debug_otp
            log.info(f"🔧 DEBUG MODE: Including OTP in response: {debug_otp}")

        return OutputSendOTPSerializer(response_data).data


class VerifyLoginOTPSerializer(UsernameFieldMixin, CountryAlpha2Mixin):
    """
    Serializer for verifying OTP and logging in the user
    """

    RETURN_USER_OBJECT = False
    otp = serializers.CharField()

    def validate(self, attrs):
        country = attrs.get("country_alpha2", None)
        user_repository = UserService()
        username = user_repository.check_and_repair_username(username=attrs["username"], country=country)

        # Verify OTP
        otp_generator = OTPGenerator(user_identifier=username, otp=attrs["otp"])
        if not otp_generator.verify_otp():
            raise ValidationError(_("Invalid or expired code. Please request a new code."))

        # Check if user exists
        user = user_repository.get_user_by_username(username)
        if not user:
            raise ValidationError(_("User not found"))

        # Invalidate OTP after successful verification
        otp_generator.invalidate_otp_in_cache()

        attrs["username"] = username
        attrs["user"] = user
        return attrs

    def to_representation(self, instance):
        user = self.validated_data.get("user")

        # Generate tokens for the user
        auth_backend = TainoAuthenticationBackend()
        tokens = auth_backend.get_user_tokens_data(user)

        return {
            "message": _("Login successful"),
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
        }


class VerifyAuthenticationSerializer(TainoBaseSerializer):
    """
    Serializer to verify if user is authenticated
    """
    is_authenticated = serializers.BooleanField(read_only=True)
    user = OutputUserProfileModelSerializer(read_only=True)
