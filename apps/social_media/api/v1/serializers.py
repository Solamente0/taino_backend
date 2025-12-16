from rest_framework import serializers

from apps.social_media.models import SocialMediaType
from base_utils.serializers.base import TainoBaseModelSerializer


class SocialMediaTypeListSerializer(TainoBaseModelSerializer):
    file = serializers.FileField()

    class Meta:
        model = SocialMediaType
        fields = [
            "pid",
            "type",
            "link",
            "file",
        ]
