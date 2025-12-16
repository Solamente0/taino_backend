from rest_framework import serializers

from apps.common.models.about_us import AboutUs, AboutUsTeamMember
from base_utils.serializers.base import TainoBaseModelSerializer


class AboutUsTeamMemberSerializer(TainoBaseModelSerializer):
    avatar = serializers.FileField(source="avatar.file", required=False, allow_null=True)

    class Meta:
        model = AboutUsTeamMember
        fields = ["pid", "full_name", "job_title", "resume_link", "avatar", "order", "created_at", "updated_at"]
        read_only_fields = ["pid", "created_at", "updated_at"]


class AboutUsSerializer(TainoBaseModelSerializer):
    team_members = AboutUsTeamMemberSerializer(many=True, read_only=True)

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
            "team_members",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["pid", "created_at", "updated_at"]
