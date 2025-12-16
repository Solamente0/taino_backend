from apps.common.models import ContactUs, Newsletter
from base_utils.serializers.base import TainoBaseModelSerializer


class NewsletterAdminSerializer(TainoBaseModelSerializer):
    class Meta:
        model = Newsletter
        fields = ["pid", "email", "unsubscribe_token", "is_active", "created_at", "updated_at"]
        read_only_fields = ["pid", "email", "unsubscribe_token", "created_at", "updated_at"]
