from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.banner.models import Banner
from apps.document.models import TainoDocument
from apps.document.services.query import TainoDocumentQuery
from base_utils.serializers.base import TainoBaseModelSerializer


class BannerAdminListSerializer(TainoBaseModelSerializer):
    file = serializers.SerializerMethodField()
    banner_type_display = serializers.CharField(source="get_banner_type_display", read_only=True)

    class Meta:
        model = Banner
        fields = [
            "pid",
            "banner_type",
            "banner_type_display",
            "file",
            "iframe_code",
            "iframe_height",
            "display_duration",  # اضافه شد
            "is_active",
            "where_to_place",
            "header_text",
            "bold_text",
            "footer_text",
            "link_title",
            "link",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_file(self, obj):
        if obj.file and hasattr(obj.file, "file"):
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.file.url)
            return obj.file.file.url
        return None


class BannerAdminCreateUpdateSerializer(TainoBaseModelSerializer):
    file = serializers.SlugRelatedField(
        queryset=TainoDocumentQuery().get_visible_for_create_update(), slug_field="pid", required=False, allow_null=True
    )

    class Meta:
        model = Banner
        fields = [
            "pid",
            "banner_type",
            "file",
            "iframe_code",
            "iframe_height",
            "display_duration",  # اضافه شد
            "is_active",
            "where_to_place",
            "header_text",
            "bold_text",
            "footer_text",
            "link_title",
            "link",
            "order",
        ]
        read_only_fields = ["pid"]

    def validate(self, attrs):
        """
        اعتبارسنجی بر اساس نوع بنر
        """
        banner_type = attrs.get("banner_type", "image")
        file = attrs.get("file")
        iframe_code = attrs.get("iframe_code")

        # برای بنر تصویری، فایل الزامی است
        if banner_type == "image" and not file:
            if not self.instance or not self.instance.file:
                raise serializers.ValidationError({"file": "برای بنر تصویری، فایل الزامی است."})

        # برای بنر iframe/embed، کد الزامی است
        if banner_type in ["iframe", "embed"] and not iframe_code:
            if not self.instance or not self.instance.iframe_code:
                raise serializers.ValidationError({"iframe_code": "برای بنر iframe/embed، کد الزامی است."})

        return attrs

    def to_representation(self, instance):
        return BannerAdminListSerializer(instance=instance, context=self.context).data
