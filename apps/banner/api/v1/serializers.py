from rest_framework import serializers

from apps.banner.models import Banner
from base_utils.serializers.base import TainoBaseModelSerializer


class BannerListSerializer(TainoBaseModelSerializer):
    file = serializers.SerializerMethodField()

    class Meta:
        model = Banner
        fields = [
            "pid",
            "order",
            "banner_type",
            "link",
            "file",
            "iframe_code",
            "iframe_height",
            "display_duration",  # اضافه شد
            "header_text",
            "bold_text",
            "footer_text",
            "link_title",
            "where_to_place"
        ]

    def get_file(self, obj):
        """
        فقط برای بنرهای تصویری، URL فایل رو برمی‌گردونیم
        """
        if obj.banner_type == 'image' and obj.file:
            request = self.context.get('request')
            if request and hasattr(obj.file, 'file'):
                return request.build_absolute_uri(obj.file.file.url)
            elif hasattr(obj.file, 'file'):
                return obj.file.file.url
        return None
