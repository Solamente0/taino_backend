from rest_framework import serializers

from apps.common.models import ServiceItem
from base_utils.serializers.base import TainoBaseModelSerializer
from rest_framework import serializers

from apps.common.models import ServiceItem, ServiceCategory
from apps.document.models import TainoDocument
from base_utils.serializers.base import TainoBaseModelSerializer


class ServiceCategoryAdminSerializer(TainoBaseModelSerializer):
    icon = serializers.SlugRelatedField(queryset=TainoDocument.objects.all(), slug_field="pid", required=False, allow_null=True)

    class Meta:
        model = ServiceCategory
        fields = [
            "pid",
            "static_name",
            "name",
            "description",
            "icon",
            "order",
            "is_active",
            "created_at",
            "updated_at",
            "soon",
        ]
        read_only_fields = ["pid", "created_at", "updated_at"]


class ServiceItemAdminSerializer(TainoBaseModelSerializer):
    icon = serializers.SlugRelatedField(queryset=TainoDocument.objects.all(), slug_field="pid", required=False, allow_null=True)
    category = serializers.SlugRelatedField(
        queryset=ServiceCategory.objects.all(), slug_field="pid", required=False, allow_null=True
    )
    category_details = ServiceCategoryAdminSerializer(source="category", read_only=True)

    class Meta:
        model = ServiceItem
        fields = [
            "pid",
            "category",
            "category_details",
            "static_name",
            "name",
            "description",
            "icon",
            "soon",
            "order",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["pid", "created_at", "updated_at", "category_details"]
