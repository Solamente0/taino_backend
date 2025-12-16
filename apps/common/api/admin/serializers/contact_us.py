from apps.common.models import ContactUs
from base_utils.serializers.base import TainoBaseModelSerializer


class ContactUsAdminSerializer(TainoBaseModelSerializer):
    class Meta:
        model = ContactUs
        fields = ["pid", "name", "email", "phone", "subject", "message", "is_read", "created_at", "updated_at"]
        read_only_fields = ["pid", "name", "email", "phone", "subject", "message", "created_at", "updated_at"]
