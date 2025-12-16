from rest_framework import serializers

from apps.common.models.about_us import AboutUs, AboutUsTeamMember
from apps.document.models import TainoDocument
from base_utils.serializers.base import TainoBaseModelSerializer


class AboutUsTeamMemberAdminSerializer(TainoBaseModelSerializer):
    avatar = serializers.SlugRelatedField(
        queryset=TainoDocument.objects.all(), slug_field="pid", required=False, allow_null=True
    )

    class Meta:
        model = AboutUsTeamMember
        fields = [
            "pid",
            "about_us",
            "full_name",
            "job_title",
            "resume_link",
            "avatar",
            "order",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["pid", "created_at", "updated_at"]


class AboutUsAdminSerializer(TainoBaseModelSerializer):

    class Meta:
        model = AboutUs
        fields = [
            "pid",
            "title",
            "history",
            "values",
            "services",
            "team_description",
            "extra",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["pid", "created_at", "updated_at"]
