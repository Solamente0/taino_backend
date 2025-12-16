from rest_framework import serializers

from apps.common.models import (
    HomePage,
    HeroSectionImage,
    PartnerShip,
    WayToFileTax,
    Service,
    TeamMember,
    Testimonial,
    FrequentlyAskedQuestion,
    TermsOfUse,
    Newsletter,
    ContactUs,
)
from apps.document.models import TainoDocument
from base_utils.serializers.base import TainoBaseModelSerializer


class HomePageAdminSerializer(TainoBaseModelSerializer):
    class Meta:
        model = HomePage
        fields = [
            "pid",
            "header_title",
            "header_sub_title",
            "why",
            "why_point1",
            "why_point2",
            "why_point3",
            "why_point4",
            "how_to_file_tax_title",
            "how_to_file_tax_short_description",
            "corporate_strategy_img",
            "corporate_strategy_title",
            "corporate_strategy_description",
            "corporate_strategy_section1",
            "corporate_strategy_section1_des",
            "corporate_strategy_section2",
            "corporate_strategy_section2_des",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["pid", "created_at", "updated_at"]


class HeroSectionImageAdminSerializer(TainoBaseModelSerializer):
    image = serializers.SlugRelatedField(queryset=TainoDocument.objects.all(), slug_field="pid")

    class Meta:
        model = HeroSectionImage
        fields = ["pid", "home_page", "image", "order", "created_at", "updated_at"]
        read_only_fields = ["pid", "created_at", "updated_at"]


class PartnerShipAdminSerializer(TainoBaseModelSerializer):
    image = serializers.SlugRelatedField(queryset=TainoDocument.objects.all(), slug_field="pid")

    class Meta:
        model = PartnerShip
        fields = ["pid", "home_page", "image", "order", "created_at", "updated_at"]
        read_only_fields = ["pid", "created_at", "updated_at"]


class WayToFileTaxAdminSerializer(TainoBaseModelSerializer):
    image = serializers.SlugRelatedField(queryset=TainoDocument.objects.all(), slug_field="pid")

    class Meta:
        model = WayToFileTax
        fields = ["pid", "home_page", "title", "description", "image", "order", "is_active", "created_at", "updated_at"]
        read_only_fields = ["pid", "created_at", "updated_at"]


class ServiceAdminSerializer(TainoBaseModelSerializer):
    logo = serializers.SlugRelatedField(queryset=TainoDocument.objects.all(), slug_field="pid")

    class Meta:
        model = Service
        fields = ["pid", "home_page", "title", "description", "logo", "order", "is_active", "created_at", "updated_at"]
        read_only_fields = ["pid", "created_at", "updated_at"]


class TeamMemberAdminSerializer(TainoBaseModelSerializer):
    image = serializers.SlugRelatedField(
        queryset=TainoDocument.objects.all(), slug_field="pid", required=False, allow_null=True
    )

    class Meta:
        model = TeamMember
        fields = [
            "pid",
            "team_type",
            "first_name",
            "last_name",
            "title",
            "university",
            "short_brief",
            "image",
            "linkedin",
            "twitter",
            "facebook",
            "order",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["pid", "created_at", "updated_at"]


class TestimonialAdminSerializer(TainoBaseModelSerializer):
    profile_img = serializers.SlugRelatedField(
        queryset=TainoDocument.objects.all(), slug_field="pid", required=False, allow_null=True
    )

    class Meta:
        model = Testimonial
        fields = [
            "pid",
            "first_name",
            "last_name",
            "role",
            "city",
            "profile_img",
            "rating",
            "comment",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["pid", "created_at", "updated_at"]
