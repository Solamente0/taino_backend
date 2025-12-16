from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny

from base_utils.permissions import HasTainoMobileUserPermission
from .filters import UserFilterBacked
from .serializers import (
    InputUserProfileModelSerializer,
    UserProfileSerializer,
    UserProfileCreateUpdateSerializer,
    CombinedUserProfileSerializer,
    AddressSerializer,
    AddressCreateUpdateSerializer,
    DeviceDeactivateSerializer,
    UserDeviceSerializer,
    DeviceActivateSerializer,
    UserDeviceUpdateSerializer,
)
from apps.user.services.delete_account import DeleteAccountService
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from .serializers import OutputUserProfileModelSerializer, UserRoleSerializer, CurrentUserRoleSerializer
from base_utils.views.mobile import TainoMobileGenericViewSet, TainoMobileAPIView
from apps.authentication.models import UserProfile, UserDevice
from apps.address.models import Address
from ...services import DeviceService
from ...services.query.roles import UserRoleService

User = get_user_model()


class UserProfileModelViewSetAPI(TainoMobileGenericViewSet):
    queryset = User.objects.all()
    filter_backends = (UserFilterBacked,)

    @extend_schema(request=InputUserProfileModelSerializer, responses={200: OutputUserProfileModelSerializer})
    @action(detail=False, methods=["GET", "PATCH"], url_path="profile", url_name="profile")
    def profile(self, request, *args, **kwargs):
        if self.request.method == "GET":
            output = OutputUserProfileModelSerializer(instance=request.user, context={"request": request})
            return Response(output.data, status=status.HTTP_200_OK)

        input_serializer = InputUserProfileModelSerializer(
            instance=request.user, data=request.data, partial=True, context={"request": request}
        )
        input_serializer.is_valid(raise_exception=True)
        input_serializer.update(instance=request.user, validated_data=input_serializer.validated_data)
        output = input_serializer.data
        return Response(output, status=status.HTTP_200_OK)

    @extend_schema(request=AddressCreateUpdateSerializer, responses={201: AddressSerializer})
    @action(detail=False, methods=["POST"], url_path="add-address", url_name="add_address")
    def add_address(self, request, *args, **kwargs):
        """Create a new address for the user"""
        serializer = AddressCreateUpdateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # Create the address with the current user as creator
        address = serializer.save(creator=request.user)

        return Response(AddressSerializer(address, context={"request": request}).data, status=status.HTTP_201_CREATED)

    @extend_schema(responses={200: AddressSerializer(many=True)})
    @action(detail=False, methods=["GET"], url_path="addresses", url_name="get_addresses")
    def get_addresses(self, request, *args, **kwargs):
        """Get all addresses for the current user"""
        addresses = Address.objects.filter(creator=request.user)
        serializer = AddressSerializer(addresses, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=AddressCreateUpdateSerializer, responses={200: AddressSerializer})
    @action(detail=True, methods=["PUT", "PATCH"], url_path="update-address", url_name="update_address")
    def update_address(self, request, pid=None, *args, **kwargs):
        """Update an existing address"""
        try:
            address = Address.objects.get(pid=pid, creator=request.user)
        except Address.DoesNotExist:
            return Response({"detail": "Address not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = AddressCreateUpdateSerializer(
            address, data=request.data, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        updated_address = serializer.save()

        return Response(
            AddressSerializer(updated_address, context=self.get_serializer_context()).data, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["DELETE"], url_path="delete-address", url_name="delete_address")
    def delete_address(self, request, pid=None, *args, **kwargs):
        """Delete an address"""
        try:
            address = Address.objects.get(pid=pid, creator=request.user)
        except Address.DoesNotExist:
            return Response({"detail": "Address not found"}, status=status.HTTP_404_NOT_FOUND)

        address.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserRolesViewSet(TainoMobileGenericViewSet):
    """
    ViewSet for user roles
    """

    serializer_class = UserRoleSerializer

    def get_permissions(self):
        if self.action == "all_roles":
            return []
        else:
            return [IsAuthenticated(), HasTainoMobileUserPermission()]

    @extend_schema(responses={200: CurrentUserRoleSerializer})
    @action(detail=False, methods=["GET"], url_path="my-roles", url_name="my_roles")
    def my_roles(self, request, *args, **kwargs):
        """
        Get current user's roles
        """
        serializer = CurrentUserRoleSerializer(instance=request.user, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(responses={200: UserRoleSerializer(many=True)})
    @action(detail=False, methods=["GET"], url_path="all", url_name="all_roles")
    def all_roles(self, request, *args, **kwargs):
        """
        Get all available user roles
        """

        roles = UserRoleService.get_available_roles()
        serializer = self.get_serializer(roles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserProfileViewSet(TainoMobileGenericViewSet):
    """
    ViewSet for managing user profiles
    """

    parser_classes = [*TainoMobileGenericViewSet.parser_classes, MultiPartParser, FormParser]

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    def get_object(self):
        """
        Get or create profile for the current user
        """
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update", "update_profile"]:
            return UserProfileCreateUpdateSerializer
        return UserProfileSerializer

    @extend_schema(responses={200: CombinedUserProfileSerializer})
    @action(detail=False, methods=["GET"], url_path="get-profile")
    def get_profile(self, request):
        """
        Get profile for the current user
        """
        instance = self.get_object()
        return Response(CombinedUserProfileSerializer(instance, context=self.get_serializer_context()).data)

    @extend_schema(request=UserProfileCreateUpdateSerializer, responses={200: CombinedUserProfileSerializer})
    @action(detail=False, methods=["PUT", "PATCH"], url_path="update-profile")
    def update_profile(self, request):
        """
        Create or update profile for the current user
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        instance.refresh_from_db()
        # Use the combined serializer for the response
        return Response(
            CombinedUserProfileSerializer(instance, context=self.get_serializer_context()).data, status=status.HTTP_200_OK
        )


class DeleteAccountAPIView(TainoMobileAPIView):
    def post(self, request, *args, **kwargs):
        user = self.request.user
        ds = DeleteAccountService(user=user)
        ds.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserDeviceViewSet(TainoMobileGenericViewSet):
    """
    ViewSet for managing user devices.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserDeviceSerializer

    def get_queryset(self):
        """Return only the current user's devices"""
        return UserDevice.objects.filter(user=self.request.user).order_by("-last_login")

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return UserDeviceUpdateSerializer
        elif self.action == "activate":
            return DeviceActivateSerializer
        elif self.action == "deactivate":
            return DeviceDeactivateSerializer
        return UserDeviceSerializer

    @extend_schema(responses={200: UserDeviceSerializer(many=True)})
    def list(self, request, *args, **kwargs):
        """List all devices for the current user"""
        devices = DeviceService.get_user_devices(request.user)
        serializer = self.get_serializer(devices, many=True)
        return Response(serializer.data)

    @extend_schema(responses={200: UserDeviceSerializer})
    @action(detail=False, methods=["GET"], url_path="active")
    def active_device(self, request, *args, **kwargs):
        """Get the currently active device for the user"""
        device = DeviceService.get_active_device(request.user)
        if device:
            serializer = self.get_serializer(device)
            return Response(serializer.data)
        return Response({"detail": "No active device found"}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(request=DeviceActivateSerializer, responses={200: UserDeviceSerializer})
    @action(detail=False, methods=["POST"], url_path="activate")
    def activate(self, request, *args, **kwargs):
        """Activate a specific device and deactivate all others"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device = DeviceService.activate_device(user=request.user, device_id=serializer.validated_data["device_id"])

        return Response(UserDeviceSerializer(device).data)

    @extend_schema(request=DeviceDeactivateSerializer, responses={200: dict})
    @action(detail=False, methods=["POST"], url_path="deactivate")
    def deactivate(self, request, *args, **kwargs):
        """Deactivate a specific device"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        success = DeviceService.deactivate_device(user=request.user, device_id=serializer.validated_data["device_id"])

        if success:
            return Response({"detail": "Device deactivated successfully"})
        return Response({"detail": "Device not found"}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(responses={200: dict})
    @action(detail=False, methods=["POST"], url_path="deactivate-all", permission_classes=[], authentication_classes=[])
    def deactivate_all(self, request, *args, **kwargs):
        """Deactivate all devices for the current user"""
        # user = request.user
        data = request.data
        if "username" in data:
            phone_number = data.get("username")[1:]
            user = User.objects.get(phone_number=phone_number)

            print(f"datat==== {data=}", flush=True)
            print(f"user==== {user=}", flush=True)

            count = DeviceService.deactivate_all_devices(user)

            # Remove all refresh tokens from user
            from base_utils.jwt import blacklist_all_user_tokens

            tokens_blacklisted = blacklist_all_user_tokens(user)
            print(f"tokens_blacklisted==== {tokens_blacklisted=}", flush=True)

            return Response({"message": f"{count} devices deactivated successfully"})
        return Response({}, status=status.HTTP_200_OK)
