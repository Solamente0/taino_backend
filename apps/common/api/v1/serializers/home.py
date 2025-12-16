from rest_framework import serializers

from apps.common.models import HomePage, HeroSectionImage, PartnerShip, WayToFileTax, Service, TeamMember, Testimonial
from base_utils.serializers.base import TainoBaseModelSerializer


class HeroSectionImageSerializer(TainoBaseModelSerializer):
    image = serializers.FileField(source="image.file")

    class Meta:
        model = HeroSectionImage
        fields = ["image"]


class PartnerShipSerializer(TainoBaseModelSerializer):
    image = serializers.FileField(source="image.file")

    class Meta:
        model = PartnerShip
        fields = ["image"]


class WayToFileTaxSerializer(TainoBaseModelSerializer):
    image = serializers.FileField(source="image.file")

    class Meta:
        model = WayToFileTax
        fields = ["image", "title", "description"]


class ServiceSerializer(TainoBaseModelSerializer):
    logo = serializers.FileField(source="logo.file")

    class Meta:
        model = Service
        fields = ["logo", "title", "description"]


class TeamMemberSerializer(TainoBaseModelSerializer):
    image = serializers.FileField(source="image.file")

    class Meta:
        model = TeamMember
        fields = ["first_name", "last_name", "title", "university", "short_brief", "image", "linkedin", "twitter", "facebook"]


class TestimonialSerializer(TainoBaseModelSerializer):
    profile_img = serializers.FileField(source="profile_img.file")
    user = serializers.SerializerMethodField()
    ratting = serializers.IntegerField(source="rating")  # To match the JSON format

    class Meta:
        model = Testimonial
        fields = ["user", "ratting", "comment"]

    def get_user(self, obj):
        return {
            "first_name": obj.first_name,
            "last_name": obj.last_name,
            "profile_img": obj.profile_img.file.url if obj.profile_img else None,
            "city": obj.city,
            "role": obj.role,
        }


class CorporateStrategySerializer(serializers.Serializer):
    img1 = serializers.URLField(source="corporate_strategy_img.file.url")
    title = serializers.CharField(source="corporate_strategy_title")
    description = serializers.CharField(source="corporate_strategy_description")
    section1 = serializers.CharField(source="corporate_strategy_section1")
    section1_des = serializers.CharField(source="corporate_strategy_section1_des")
    section2 = serializers.CharField(source="corporate_strategy_section2")
    section2_des = serializers.CharField(source="corporate_strategy_section2_des")


class HomePageSerializer(TainoBaseModelSerializer):
    hero_section_images = serializers.SerializerMethodField()
    partner_ships = serializers.SerializerMethodField()
    way_to_file_tax = WayToFileTaxSerializer(many=True, read_only=True)
    services = ServiceSerializer(many=True, read_only=True)
    testimonials = TestimonialSerializer(many=True, read_only=True, source="testimonial_set")
    corporate_strategy = serializers.SerializerMethodField()
    team_members = serializers.SerializerMethodField()

    class Meta:
        model = HomePage
        fields = [
            "header_title",
            "header_sub_title",
            "why",
            "why_point1",
            "why_point2",
            "why_point3",
            "why_point4",
            "how_to_file_tax_title",
            "how_to_file_tax_short_description",
            "hero_section_images",
            "partner_ships",
            "way_to_file_tax",
            "services",
            "testimonials",
            "corporate_strategy",
            "team_members",
        ]

    def get_hero_section_images(self, obj):
        hero_images = HeroSectionImage.objects.filter(home_page=obj)
        return [image.image.file.url for image in hero_images]

    def get_partner_ships(self, obj):
        partnerships = PartnerShip.objects.filter(home_page=obj)
        return [partnership.image.file.url for partnership in partnerships]

    def get_corporate_strategy(self, obj):
        if obj.corporate_strategy_img:
            return CorporateStrategySerializer(obj).data
        return None

    def get_team_members(self, obj):
        result = {}

        executive_team = TeamMember.objects.filter(team_type="executive_team", is_active=True)
        accounting_affiliates = TeamMember.objects.filter(team_type="accounting_affiliates", is_active=True)

        result["executive_team"] = TeamMemberSerializer(executive_team, many=True).data
        result["accounting_affiliates"] = TeamMemberSerializer(accounting_affiliates, many=True).data

        return result
