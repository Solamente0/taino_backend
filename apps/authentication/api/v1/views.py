from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

import config.settings.constants
from apps.authentication.api.v1.serializers import (
    HasPasswordSerializer,
    ChangePasswordSerializer,
    OutputMessageSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    OutputCredentialSerializer,
    SetEmailSerializer,
    RegisterSerializer,
    SetUserPasswordSerializer,
    SendOTPSerializer,
    VerifyOTPSerializer,
    OutputVerifyOTPSerializer,
    OutputSendOTPSerializer,
    CustomTokenObtainPairSerializer,
    SendRegistrationCodeSerializer,
    SetNumberSerializer,
    SendForgotPasswordOTPSerializer,
    CustomTokenRefreshSerializer,
    LogoutSerializer,
    CheckUserExistsSerializer,
    OutputUserExistsSerializer,
    SendLoginOTPSerializer,
    VerifyLoginOTPSerializer,
)
from apps.authentication.api.v1.serializers import VerifyAuthenticationSerializer
from apps.authentication.permissions import SingleDevicePermission
from apps.authentication.services.auth import TainoGoogleAuthenticationBackend, NoExceptionJWTAuthentication
from apps.authentication.services.google_auth import GoogleAuth
from apps.user.api.v1.serializers import OutputUserProfileModelSerializer  # todo fix import
from apps.user.services import DeviceService
from base_utils.permissions import HasTainoMobileUserPermission
from base_utils.views.mobile import TainoMobileGenericViewSet

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_scope = "auth"


class TainoAuthFlowViewSet(TainoMobileGenericViewSet):
    queryset = None
    permission_classes = [IsAuthenticated]
    throttle_scope = "auth"

    def get_serializer_class(self):
        if self.action == "send_otp":
            return SendOTPSerializer
        if self.action == "send_registration_code":
            return SendRegistrationCodeSerializer
        if self.action == "verify_otp":
            return VerifyOTPSerializer
        if self.action == "register":
            return RegisterSerializer
        if self.action == "login":
            return LoginSerializer
        if self.action == "has_password":
            return HasPasswordSerializer
        if self.action == "change_password":
            return ChangePasswordSerializer

        if self.action == "send_forgot_password_code":
            return SendForgotPasswordOTPSerializer
        if self.action == "forgot_password":
            return ForgotPasswordSerializer
        if self.action == "set_email":
            return SetEmailSerializer
        if self.action == "set_phone_number":
            return SetNumberSerializer
        if self.action == "set_password":
            return SetUserPasswordSerializer
        if self.action == "check_user_exists":
            return CheckUserExistsSerializer
        if self.action == "send_login_otp":
            return SendLoginOTPSerializer
        if self.action == "verify_login_otp":
            return VerifyLoginOTPSerializer
        return super(TainoAuthFlowViewSet, self).get_serializer_class()

    def get_permissions(self):
        if self.action == "send_otp":
            return [AllowAny()]
        if self.action == "verify_otp":
            return [AllowAny()]
        if self.action == "send_registration_code":
            return [AllowAny()]
        if self.action == "register":
            return [AllowAny()]
        if self.action == "login":
            # return [AllowAny(), SingleDevicePermission()]
            return [AllowAny()]
        if self.action == "has_password":
            return [IsAuthenticated(), HasTainoMobileUserPermission()]
        if self.action == "change_password":
            return [IsAuthenticated(), HasTainoMobileUserPermission()]
        if self.action == "send_forgot_password_code":
            return [AllowAny()]
        if self.action == "forgot_password":
            return [AllowAny()]
        if self.action == "verify_auth":
            return [AllowAny()]
        if self.action == "set_email":
            return [IsAuthenticated(), HasTainoMobileUserPermission()]
        if self.action == "set_phone_number":
            return [IsAuthenticated(), HasTainoMobileUserPermission()]
        if self.action == "set_password":
            return [IsAuthenticated(), HasTainoMobileUserPermission()]
        if self.action == "check_user_exists":
            return [AllowAny()]
        if self.action == "send_login_otp":
            return [AllowAny()]
        if self.action == "verify_login_otp":
            return [AllowAny()]
        return super(TainoAuthFlowViewSet, self).get_permissions()

    def get_client_ip(self, request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def set_device(self, user: User):
        request = self.request
        # Get or generate device ID
        device_id = request.COOKIES.get("device_id")
        if not device_id:
            device_id = request.META.get("HTTP_X_DEVICE_ID")
        if not device_id:
            device_id = DeviceService.generate_device_id()

        # Get user agent and IP
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        ip_address = self.get_client_ip(request)

        # Register the device
        DeviceService.register_device(user, device_id, user_agent, ip_address)
        return device_id

    # @method_decorator(*get_ratelimit(name="SendOTP", config=True))
    @extend_schema(request=SendOTPSerializer, responses={200: OutputSendOTPSerializer})
    @action(detail=False, name="send_otp", methods=["POST"], url_path="send-otp", url_name="send-otp-api")
    def send_otp(self, request, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=SendRegistrationCodeSerializer, responses={200: OutputSendOTPSerializer})
    @action(
        detail=False,
        name="send_registration_code",
        methods=["POST"],
        url_path="send-register-code",
        url_name="send_registration_code",
    )
    def send_registration_code(self, request, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.data, status=status.HTTP_202_ACCEPTED)

    @extend_schema(request=SendForgotPasswordOTPSerializer, responses={200: OutputSendOTPSerializer})
    @action(
        detail=False,
        name="send_forgot_password_code",
        methods=["POST"],
        url_path="send-forgot-password-code",
        url_name="send_forgot_password_code",
    )
    def send_forgot_password_code(self, request, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.data, status=status.HTTP_202_ACCEPTED)

    # @method_decorator(*get_ratelimit(name="VerifyOTP", config=True))
    @extend_schema(request=VerifyOTPSerializer, responses={200: OutputVerifyOTPSerializer})
    @action(detail=False, name="verify_otp", methods=["POST"], url_path="verify-otp", url_name="verify-otp-api")
    def verify_otp(self, request, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.data, status=status.HTTP_202_ACCEPTED)

    #     @method_decorator(*get_ratelimit(name="Register", config=True))
    @extend_schema(request=RegisterSerializer, responses={200: OutputCredentialSerializer})
    @action(detail=False, name="register", methods=["POST"], url_path="register", url_name="register-api")
    def register(self, request, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.create(validated_data=serializer.validated_data)
        # serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    #     @method_decorator(*get_ratelimit(name="Login", config=True))
    @extend_schema(request=LoginSerializer, responses={200: OutputCredentialSerializer})
    @action(detail=False, name="login", methods=["POST"], url_path="login", url_name="login-api")
    def login(self, request, **kwargs):
        data = request.data
        if "username" in data:
            phone_number = data.get("username")[1:]
            try:
                user = User.objects.get(phone_number=phone_number)
            except User.DoesNotExist:
                print(f"User with {phone_number} not found!", flush=True)
                raise NotFound(_("کاربری با این شماره تلفن پیدا نشد!"))

            except Exception as e:
                print(f"exception in line 205 login method: {e=}", flush=True)
                raise ValidationError(_("خطایی رخ داد!"))
        else:
            raise ValidationError("شماره تلفن وارد نشده است!")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device_id = self.set_device(user)
        response = Response(serializer.data, status=status.HTTP_200_OK)
        if not request.COOKIES.get("device_id"):
            response.set_cookie("device_id", device_id, max_age=31536000, httponly=True)  # samesite="Lax")

        return response

    @extend_schema(request=SendLoginOTPSerializer, responses={200: OutputSendOTPSerializer})
    @action(detail=False, name="send_login_otp", methods=["POST"], url_path="send-login-otp", url_name="send-login-otp-api")
    def send_login_otp(self, request, **kwargs):
        """
        Send OTP code to existing user for login
        Validates that user exists before sending OTP
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=VerifyLoginOTPSerializer, responses={200: OutputCredentialSerializer})
    @action(
        detail=False, name="verify_login_otp", methods=["POST"], url_path="verify-login-otp", url_name="verify-login-otp-api"
    )
    def verify_login_otp(self, request, **kwargs):
        """
        Verify OTP code and login user
        Returns access and refresh tokens on successful verification
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get user from validated data for device tracking
        user = serializer.validated_data.get("user")

        # Set device for the logged-in user
        device_id = self.set_device(user)

        response = Response(serializer.data, status=status.HTTP_200_OK)

        # Set device cookie if not already set
        if not request.COOKIES.get("device_id"):
            response.set_cookie("device_id", device_id, max_age=31536000, httponly=True)

        return response

    @extend_schema(responses={200: VerifyAuthenticationSerializer})
    @action(
        detail=False,
        name="verify_auth",
        methods=["GET"],
        url_path="verify-auth",
        url_name="verify-auth-api",
    )
    def verify_auth(self, request, **kwargs):
        """
        Verify if the current request has valid authentication
        Returns user data if authenticated, otherwise returns is_authenticated=False
        """
        # Use the optional JWT authentication
        auth = NoExceptionJWTAuthentication()

        try:
            user_auth = auth.authenticate(request)

            if user_auth is not None:
                user, token = user_auth

                if user and user.is_authenticated and user.is_active:
                    from apps.user.api.v1.serializers import OutputUserProfileModelSerializer

                    user_data = OutputUserProfileModelSerializer(instance=user, context={"request": request}).data

                    return Response({"is_authenticated": True, "user": user_data}, status=status.HTTP_200_OK)
        except Exception as e:
            pass

        return Response({"is_authenticated": False, "user": None}, status=status.HTTP_200_OK)

    #
    # @extend_schema(request=LoginSerializer, responses={200: OutputCredentialSerializer})
    # @action(detail=False, name="login", methods=["POST"], url_path="login", url_name="login-api")
    # def login(self, request, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #
    #     return Response(serializer.data, status=status.HTTP_200_OK)

    # @method_decorator(*get_ratelimit(name="HasPassword", config=True))
    @extend_schema(responses={200: HasPasswordSerializer}, request=None)
    @action(detail=False, name="has_password", methods=["POST"], url_path="has-password", url_name="has-password-api")
    def has_password(self, request, **kwargs):
        user = request.user
        has_password = user.has_usable_password()
        return Response(HasPasswordSerializer({"has_password": has_password}).data, status=status.HTTP_200_OK)

    # @method_decorator(*get_ratelimit(name="ChangePassword", config=True))
    @extend_schema(responses={200: ChangePasswordSerializer})
    @action(
        detail=False, name="change_password", methods=["POST"], url_path="change-password", url_name="change-password-api"
    )
    def change_password(self, request, **kwargs):
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        serializer.update(instance=request.user, validated_data=serializer.validated_data)

        output = OutputMessageSerializer(instance={"message": _("Password changed successfully")})

        return Response(output.data, status=status.HTTP_200_OK)

    # @method_decorator(*get_ratelimit(name="ForgotPassword", config=True))
    @extend_schema(responses={200: ForgotPasswordSerializer})
    @action(
        detail=False, name="forgot_password", methods=["POST"], url_path="forgot-password", url_name="forgot-password-api"
    )
    def forgot_password(self, request, **kwargs):
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        serializer.update(instance=None, validated_data=serializer.validated_data)

        output = OutputMessageSerializer(instance={"message": _("Password changed successfully")})
        return Response(output.data, status=status.HTTP_200_OK)

    # @method_decorator(*get_ratelimit(name="SetEmail", config=True))
    @extend_schema(responses={200: OutputMessageSerializer}, request=SetEmailSerializer)
    @action(detail=False, name="set_email", methods=["POST"], url_path="set-email", url_name="set-email-api")
    def set_email(self, request, **kwargs):
        serializer = self.get_serializer(instance=request.user, data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    # @method_decorator(*get_ratelimit(name="SetEmail", config=True))
    @extend_schema(responses={200: OutputMessageSerializer}, request=SetNumberSerializer)
    @action(
        detail=False, name="set_phone_number", methods=["POST"], url_path="set-phone-number", url_name="set-phone-number-api"
    )
    def set_phone_number(self, request, **kwargs):
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        serializer.update(instance=request.user, validated_data=serializer.validated_data)
        output = OutputUserProfileModelSerializer(instance=request.user, context={"request": request})
        # output = OutputMessageSerializer(instance={"message": _("Phone Number set successfully")})

        return Response(output.data, status=status.HTTP_200_OK)

    # @method_decorator(*get_ratelimit(name="SetPassword", config=True))
    @extend_schema(responses={200: OutputMessageSerializer}, request=SetUserPasswordSerializer)
    @action(detail=False, name="set_password", methods=["POST"], url_path="set-password", url_name="set-password-api")
    def set_password(self, request, **kwargs):
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        serializer.update(instance=request.user, validated_data=serializer.validated_data)

        output = OutputMessageSerializer(instance={"message": _("Password set successfully")})

        return Response(output.data, status=status.HTTP_200_OK)

    @extend_schema(request=CheckUserExistsSerializer, responses={200: OutputUserExistsSerializer})
    @action(
        detail=False,
        name="check_user_exists",
        methods=["POST"],
        url_path="check-user-exists",
        url_name="check-user-exists-api",
    )
    def check_user_exists(self, request, **kwargs):
        """
        Check if a user exists by username (email or phone number)
        Returns: {"exists": true/false}
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class TokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer
    permission_classes = [AllowAny]
    throttle_scope = "auth"


# class LogoutView(TokenRefreshView):
#     serializer_class = LogoutSerializer
#     permission_classes = [IsAuthenticated]


@extend_schema(request=LogoutSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request, **kwargs):
    response = Response({}, 200)

    try:
        # TODO: logic
        if request.user:
            from apps.notification.models import UserNotificationToken

            UserNotificationToken.objects.filter(user=request.user, user_agent=request.data.get("user_agent", None)).delete()

            device_id = request.COOKIES.get("device_id")
            if not device_id:
                device_id = request.META.get("HTTP_X_DEVICE_ID")

            # Deactivate the current device
            if device_id:
                DeviceService.deactivate_device(request.user, device_id)

            # Create response
            # Delete device_id cookie
            if "device_id" in request.COOKIES:
                response.delete_cookie("device_id")

            # Remove all refresh tokens from user
            from base_utils.jwt import blacklist_all_user_tokens

            tokens_blacklisted = blacklist_all_user_tokens(request.user)

    except Exception as e:
        pass

    return response
