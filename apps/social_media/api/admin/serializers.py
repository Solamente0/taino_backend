from rest_framework import serializers

from apps.document.models import TainoDocument
from apps.social_media.models import SocialMediaType
from apps.social_media.services.social_media_type import SocialMediaTypeService
from base_utils.serializers.base import TainoBaseModelSerializer


class SocialMediaTypeAdminListRetrieveSerializer(TainoBaseModelSerializer):
    file = serializers.FileField()

    class Meta:
        model = SocialMediaType
        fields = ["pid", "type", "link", "file", "created_at", "updated_at", "is_active"]
        read_only_fields = fields


class SocialMediaTypeAdminCreateUpdateSerializer(TainoBaseModelSerializer):
    file = serializers.SlugRelatedField(queryset=TainoDocument.objects.all(), slug_field="pid")

    class Meta:
        model = SocialMediaType
        fields = ["type", "link", "file", "is_active"]

    def create(self, validated_data):
        instance = SocialMediaTypeService().create_social_media(**validated_data)
        return instance

    def to_representation(self, instance):
        return SocialMediaTypeAdminListRetrieveSerializer(instance=instance, context=self.context).data
