from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.country.services.query import CountryQuery
from apps.country.services.serializers_field import GlobalCountryReadOnlySerializer
from apps.document.services.query import TainoDocumentQuery
from apps.referral.models import FlatReferral
from base_utils.serializers.base import TainoBaseModelSerializer, TainoBaseSerializer

User = get_user_model()


class AdminUserMinimalSerializer(TainoBaseModelSerializer):
    avatar = serializers.FileField(allow_null=True, required=False)

    class Meta:
        model = User
        fields = (
            "pid",
            "avatar",
            "first_name",
            "last_name",
        )


class AdminUserDetailSerializer(TainoBaseModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)
    roles = serializers.SerializerMethodField(method_name="get_roles", read_only=True)
    avatar = serializers.FileField(allow_null=True, required=False)
    invited_by_user = serializers.SerializerMethodField(method_name="get_invited_by_user", read_only=True)
    # score = serializers.SerializerMethodField(method_name="get_score", read_only=True)
    phone_country = GlobalCountryReadOnlySerializer()
    country = GlobalCountryReadOnlySerializer()

    def get_roles(self, obj):
        return []

    def get_invited_by_user(self, obj):
        referral = FlatReferral.objects.filter(referred=obj).first()
        if referral:
            return AdminUserMinimalSerializer(instance=referral.referrer, context=self.context).data

        return None

    #
    # def get_score(self, obj):
    #     return get_total_loyalty_score_for_user(obj)

    class Meta:
        model = User
        fields = (
            "pid",
            "vekalat_id",
            "date_joined",
            "avatar",
            "first_name",
            "last_name",
            "full_name",
            "roles",
            "phone_number",
            "phone_country",
            "country",
            "currency",
            "email",
            "is_active",
            "has_premium_account",
            "invited_by_user",
            "is_email_verified",
            "is_phone_number_verified",
        )
        read_only_fields = fields


class AdminUserListSerializer(TainoBaseModelSerializer):
    avatar = serializers.FileField(allow_null=True, required=False)
    phone_country = GlobalCountryReadOnlySerializer()
    country = GlobalCountryReadOnlySerializer()

    class Meta:
        model = User
        fields = (
            "pid",
            "vekalat_id",
            "date_joined",
            "avatar",
            "first_name",
            "last_name",
            "phone_number",
            "phone_country",
            "country",
            "email",
            "is_active",
            "has_premium_account",
            "is_email_verified",
            "is_phone_number_verified",
        )
        read_only_fields = fields


class AdminUserCreateUpdateModelSerializer(TainoBaseModelSerializer):
    avatar = serializers.SlugRelatedField(
        queryset=TainoDocumentQuery.get_visible_for_create_update(), slug_field="pid", required=False, allow_null=True
    )
    phone_country = serializers.SlugRelatedField(
        queryset=CountryQuery.get_visible_countries(), slug_field="pid", required=False, allow_null=True
    )
    country = serializers.SlugRelatedField(
        queryset=CountryQuery.get_visible_countries(), slug_field="pid", required=False, allow_null=True
    )
    invited_by = serializers.SlugRelatedField(
        queryset=get_user_model().objects.all(),
        slug_field="pid",
        write_only=True,
        required=False,
        allow_null=True,
        default=None,
    )

    class Meta:
        model = User
        fields = (
            "avatar",
            "first_name",
            "last_name",
            "phone_number",
            "phone_country",
            "country",
            "email",
            "is_active",
            "has_premium_account",
            "is_email_verified",
            "is_phone_number_verified",
            "invited_by",
        )

    def create(self, validated_data):
        invited_by = validated_data.pop("invited_by", None)
        user = super().create(validated_data)

        if invited_by:
            FlatReferral.objects.get_or_create(referrer=invited_by, referred=user)

        return user

    def update(self, instance, validated_data):
        invited_by = validated_data.pop("invited_by", None)
        user = super().update(instance, validated_data)

        if invited_by:
            FlatReferral.objects.get_or_create(referrer=invited_by, referred=user)

        return user

    def to_representation(self, instance):
        return AdminUserDetailSerializer(instance, context=self.context).data


class AdminOutputUserProfileModelSerializer(TainoBaseModelSerializer):
    phone_country = GlobalCountryReadOnlySerializer(read_only=True)
    country = GlobalCountryReadOnlySerializer(read_only=True)
    avatar = serializers.FileField()

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
            "phone_country",
            "country",
            "has_premium_account",
            "language",
            "currency",
        ]


class AdminChangePasswordSerializer(TainoBaseSerializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
