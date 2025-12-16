from apps.common.models import TermsOfUse
from base_utils.serializers.base import TainoBaseModelSerializer


class TermsOfUseAdminSerializer(TainoBaseModelSerializer):
    class Meta:
        model = TermsOfUse
        fields = ["pid", "title", "content", "order", "is_active", "created_at", "updated_at"]
        read_only_fields = ["pid", "created_at", "updated_at"]
