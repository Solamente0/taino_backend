from rest_framework import serializers
from apps.common.models import TutorialVideo
from base_utils.serializers.base import TainoBaseModelSerializer


class TutorialVideoSerializer(TainoBaseModelSerializer):
    video_file = serializers.FileField(source="video.file", read_only=True, required=False)
    thumbnail_file = serializers.FileField(source="thumbnail.file", read_only=True, required=False)
    video_source = serializers.SerializerMethodField()
    
    class Meta:
        model = TutorialVideo
        fields = [
            "pid",
            "route_path",
            "title",
            "name",
            "description",
            "video_file",
            "video_url",
            "video_source",
            "thumbnail_file",
            "duration",
            "show_on_first_visit",
            "tags",
            "created_at",
            "updated_at"
        ]
        read_only_fields = fields
    
    def get_video_source(self, obj):
        return obj.get_video_source()


