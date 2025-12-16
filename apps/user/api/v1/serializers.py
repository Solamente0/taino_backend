from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.authentication.models import UserType, UserDevice
from apps.barlawyer.models import Bar
from apps.country.services.query import CountryQuery, StateQuery, CityQuery
from apps.country.services.serializers_field import (
    GlobalCountryReadOnlySerializer,
    GlobalStateReadOnlySerializer,
    GlobalCityReadOnlySerializer,
)
from apps.document.services.query import TainoDocumentQuery
from apps.authentication.models import UserProfile
from apps.lawyer_office.api.v1.serializers import ArchiveCabinetSerializer
from apps.address.models import Address
from base_utils.serializers.base import TainoBaseModelSerializer, TainoBaseSerializer

User = get_user_model()


class AddressSerializer(TainoBaseModelSerializer):
    """Serializer for the Address model"""

    country = GlobalCountryReadOnlySerializer(read_only=True)
    state = GlobalStateReadOnlySerializer(read_only=True)
    city = GlobalCityReadOnlySerializer(read_only=True)

    class Meta:
        model = Address
        fields = ["pid", "name", "description", "postal_code", "country", "state", "city"]
        read_only_fields = fields


class UserRoleSerializer(TainoBaseModelSerializer):
    """
    Serializer for available user roles
    """

    class Meta:
        model = UserType
        fields = ["pid", "name", "static_name", "description", "is_active"]
        read_only_fields = fields


class UsersByProviderSerializer(TainoBaseSerializer):
    """لیست کاربرانی که توسط یک کانون خاص ارائه شده‌اند"""

    bar_code = serializers.CharField(required=True, help_text="کد کانون")

    def validate_bar_code(self, value):
        try:
            bar = Bar.objects.get(code=value)
            return value
        except Bar.DoesNotExist:
            raise serializers.ValidationError("کانون با این کد یافت نشد")


class AddressCreateUpdateSerializer(TainoBaseModelSerializer):
    """Serializer for creating and updating addresses"""

    country = serializers.SlugRelatedField(
        queryset=CountryQuery.get_visible_countries(), slug_field="code", required=False, allow_null=True
    )
    state = serializers.SlugRelatedField(
        queryset=StateQuery.get_visible_states(), slug_field="pid", required=False, allow_null=True
    )
    city = serializers.SlugRelatedField(
        queryset=CityQuery.get_visible_cities(), slug_field="pid", required=False, allow_null=True
    )

    class Meta:
        model = Address
        fields = ["name", "description", "postal_code", "country", "state", "city"]

    def validate(self, attrs):
        # Validate that country and state are consistent
        if "country" in attrs and "state" in attrs and attrs["state"] is not None and attrs["country"] is not None:
            if attrs["state"].country.code != attrs["country"].code:
                raise serializers.ValidationError({"state": "State must belong to the selected country"})

        # Validate that state and city are consistent
        if "state" in attrs and "city" in attrs and attrs["city"] is not None and attrs["state"] is not None:
            if attrs["city"].state.pid != attrs["state"].pid:
                raise serializers.ValidationError({"city": "City must belong to the selected state"})

        return attrs

    def to_representation(self, instance):
        return AddressSerializer(instance, context=self.context).data


class OutputUserProfileModelSerializer(TainoBaseModelSerializer):
    country = GlobalCountryReadOnlySerializer(read_only=True)
    phone_country = GlobalCountryReadOnlySerializer(read_only=True)
    avatar = serializers.FileField()
    addresses = serializers.SerializerMethodField(read_only=True)
    role = UserRoleSerializer(read_only=True)
    provider = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            "pid",
            "first_name",
            "last_name",
            "vekalat_id",
            "phone_number",
            "avatar",
            "email",
            "country",
            "phone_country",
            "has_premium_account",
            "language",
            "currency",
            "addresses",
            "role",
            "provider",
        ]

    def get_addresses(self, obj):
        # Get all addresses associated with the user
        addresses = Address.objects.filter(creator=obj)
        return AddressSerializer(addresses, many=True, context=self.context).data

    def get_provider(self, obj):
        """نمایش اطلاعات کانون ارائه‌دهنده"""
        if obj.provider:
            return {
                "pid": obj.provider.pid,
                "name": obj.provider.name,
                "code": obj.provider.code,
                "subscription_type": obj.provider.get_subscription_type_display(),
            }
        return None


class InputUserProfileModelSerializer(TainoBaseModelSerializer):
    avatar = serializers.SlugRelatedField(
        queryset=TainoDocumentQuery().get_visible_for_create_update(), slug_field="pid", required=False, allow_null=True
    )
    language = serializers.CharField(required=False, allow_null=True, default="IR")
    currency = serializers.CharField(required=False, allow_null=True, default="IRR")
    country = serializers.SlugRelatedField(
        queryset=CountryQuery.get_visible_countries(), slug_field="pid", required=False, allow_null=True
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "avatar", "language", "country", "currency")

    def to_representation(self, instance):
        return OutputUserProfileModelSerializer(instance=instance, context=self.context).data


class CurrentUserRoleSerializer(TainoBaseModelSerializer):
    """
    Serializer for current user's roles
    """

    roles = UserRoleSerializer(many=True, read_only=True, source="user_roles")

    class Meta:
        model = User
        fields = ["pid", "first_name", "last_name", "roles"]
        read_only_fields = fields


class UserProfileSerializer(TainoBaseModelSerializer):
    """
    Serializer for user profile model
    """

    archive_cabinet = ArchiveCabinetSerializer(read_only=True)
    address = AddressSerializer(read_only=True)  # Updated to use our new AddressSerializer

    class Meta:
        model = UserProfile
        fields = [
            "pid",
            "address",
            "license_number",
            "bar_association",
            "lawyer_type",
            "office_phone",
            "office_address",
            "office_location",
            "legal_entity_name",
            "legal_entity_id",
            "legal_entity_phone",
            "is_secretary",
            "lawyer",
            "archive_cabinet",
        ]
        read_only_fields = ["pid", "archive_cabinet"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        user_role = instance.user.role.static_name if instance.user.role else None

        # Filter fields based on user role
        if user_role == "lawyer":
            # Remove legal entity and secretary fields
            for field in ["legal_entity_name", "legal_entity_id", "legal_entity_phone", "is_secretary", "lawyer"]:
                data.pop(field, None)
        elif user_role == "legal_entity":
            # Remove lawyer and secretary fields
            for field in ["license_number", "bar_association", "lawyer_type", "is_secretary", "lawyer"]:
                data.pop(field, None)
        elif user_role == "secretary":
            # Remove lawyer and legal entity fields
            for field in [
                "license_number",
                "bar_association",
                "lawyer_type",
                "legal_entity_name",
                "legal_entity_id",
                "legal_entity_phone",
            ]:
                data.pop(field, None)
        elif user_role == "client":
            # Remove all specific fields
            for field in [
                "license_number",
                "bar_association",
                "lawyer_type",
                "office_phone",
                "office_address",
                "office_location",
                "legal_entity_name",
                "legal_entity_id",
                "legal_entity_phone",
                "is_secretary",
                "lawyer",
            ]:
                data.pop(field, None)

        return data


class UserProfileCreateUpdateSerializer(TainoBaseModelSerializer):
    """
    Serializer for creating and updating user profile
    """

    first_name = serializers.CharField(source="user.first_name", required=False)
    last_name = serializers.CharField(source="user.last_name", required=False)
    # email = serializers.EmailField(source="user.email", required=False)
    # phone_number = serializers.CharField(source="user.phone_number", required=False)
    # language = serializers.CharField(source="user.language", required=False)

    # Update to use proper address integration
    address = serializers.SlugRelatedField(
        queryset=Address.objects.filter(), slug_field="pid", required=False, allow_null=True
    )
    avatar = serializers.SlugRelatedField(
        queryset=TainoDocumentQuery().get_visible_for_create_update(), slug_field="pid", required=False, allow_null=True
    )

    class Meta:
        model = UserProfile
        fields = [
            # User model fields
            "first_name",
            "last_name",
            "avatar",
            # "email",
            # "phone_number",
            # "language",
            # UserProfile model fields
            "address",
            "license_number",
            "bar_association",
            "lawyer_type",
            "office_phone",
            "office_address",
            "office_location",
            "legal_entity_name",
            "legal_entity_id",
            "legal_entity_phone",
            "is_secretary",
            "lawyer",
        ]

    def update(self, instance, validated_data):
        # Extract user data
        print(f"test::: {validated_data=}", flush=True)

        user_data = validated_data.pop("user", {})
        avatar = validated_data.pop("avatar", instance.user.avatar)
        user_data.update(avatar=avatar)
        print(f"test::: {user_data=}", flush=True)
        #
        # user_data = {
        #     "first_name": validated_data.pop("first_name", instance.first_name),
        #     "last_name": validated_data.pop("last_name", instance.last_name),
        # }
        # Update user if data exists
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
        print(f"test::: {user_data=}", flush=True)
        # Update the profile
        return super().update(instance, validated_data)

    def validate(self, attrs):
        user = self.context["request"].user
        user_role = user.role.static_name if user.role else None

        # Validate fields based on user role
        if user_role == "lawyer":
            # Validate lawyer fields
            if "license_number" in attrs and not attrs["license_number"]:
                raise serializers.ValidationError({"license_number": "License number is required for lawyers"})

        elif user_role == "legal_entity":
            # Validate legal entity fields
            if "legal_entity_name" in attrs and not attrs["legal_entity_name"]:
                raise serializers.ValidationError({"legal_entity_name": "Legal entity name is required"})
            if "legal_entity_id" in attrs and not attrs["legal_entity_id"]:
                raise serializers.ValidationError({"legal_entity_id": "Legal entity ID is required"})

        elif user_role == "secretary":
            # Validate secretary fields
            if "lawyer" in attrs and not attrs["lawyer"]:
                raise serializers.ValidationError({"lawyer": "Lawyer is required for secretaries"})

        return attrs


class CombinedUserProfileSerializer(TainoBaseModelSerializer):
    """
    Combined serializer for both User and UserProfile models
    Used for complete profile responses in the API
    """

    # User model fields
    pid = serializers.CharField(source="user.pid", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    phone_number = serializers.CharField(source="user.phone_number", read_only=True)
    # vekalat_id = serializers.CharField(source="user.vekalat_id", read_only=True)
    # language = serializers.CharField(source="user.language", read_only=True)
    # currency = serializers.CharField(source="user.currency", read_only=True)

    # Add other User model fields as needed
    avatar = serializers.FileField(source="user.avatar", read_only=True)
    country = GlobalCountryReadOnlySerializer(source="user.country", read_only=True)
    phone_country = GlobalCountryReadOnlySerializer(source="user.phone_country", read_only=True)
    has_premium_account = serializers.BooleanField(source="user.has_premium_account", read_only=True)
    archive_cabinet = ArchiveCabinetSerializer(read_only=True)

    # Address integration
    address = AddressSerializer(read_only=True)
    user_addresses = serializers.SerializerMethodField(read_only=True)
    role = UserRoleSerializer(read_only=True, source="user.role")

    def get_user_addresses(self, obj):
        # Get all addresses associated with the user
        addresses = Address.objects.filter(creator=obj.user)
        return AddressSerializer(addresses, many=True, context=self.context).data

    class Meta:
        model = UserProfile
        fields = [
            # User model fields
            "pid",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            # "vekalat_id",
            # "language",
            # "currency",
            "avatar",
            "country",
            "phone_country",
            "has_premium_account",
            # UserProfile model fields
            "address",
            "user_addresses",
            "license_number",
            "bar_association",
            "lawyer_type",
            "office_phone",
            "office_address",
            "office_location",
            "legal_entity_name",
            "legal_entity_id",
            "legal_entity_phone",
            "is_secretary",
            "lawyer",
            "archive_cabinet",
            "role",
        ]
        read_only_fields = fields


class UserDeviceSerializer(TainoBaseModelSerializer):
    """
    Serializer for UserDevice model with read-only fields.
    """

    class Meta:
        model = UserDevice
        fields = ["pid", "device_id", "device_name", "user_agent", "ip_address", "created_at", "last_login", "is_active"]
        read_only_fields = fields


class UserDeviceUpdateSerializer(TainoBaseModelSerializer):
    """
    Serializer for updating UserDevice model.
    """

    class Meta:
        model = UserDevice
        fields = ["device_name", "is_active"]


class DeviceActivateSerializer(TainoBaseSerializer):
    """
    Serializer for activating a specific device.
    """

    device_id = serializers.CharField(required=True)


class DeviceDeactivateSerializer(TainoBaseSerializer):
    """
    Serializer for deactivating a specific device.
    """

    device_id = serializers.CharField(required=True)
