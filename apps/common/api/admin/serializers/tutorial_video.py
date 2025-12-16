from rest_framework import serializers
from apps.common.models import TutorialVideo
from apps.document.models import TainoDocument
from base_utils.serializers.base import TainoBaseModelSerializer


class TutorialVideoAdminSerializer(TainoBaseModelSerializer):
    video = serializers.SlugRelatedField(
        queryset=TainoDocument.objects.all(),
        slug_field="pid",
        required=False,
        allow_null=True
    )
    
    thumbnail = serializers.SlugRelatedField(
        queryset=TainoDocument.objects.all(),
        slug_field="pid",
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = TutorialVideo
        fields = [
            "pid",
            "route_path",
            "title",
            "name",
            "description",
            "video",
            "video_url",
            "thumbnail",
            "duration",
            "order",
            "show_on_first_visit",
            "tags",
            "is_active",
            "created_at",
            "updated_at"
        ]
        read_only_fields = ["pid", "created_at", "updated_at"]
    
    def validate(self, attrs):
        # Ensure at least one video source is provided
        if not attrs.get('video') and not attrs.get('video_url'):
            raise serializers.ValidationError(
                "Either video file or video URL must be provided"
            )
        return attrs
