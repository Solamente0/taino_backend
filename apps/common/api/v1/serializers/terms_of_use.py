from apps.common.models import TermsOfUse
from base_utils.serializers.base import TainoBaseModelSerializer


class TermsOfUseSerializer(TainoBaseModelSerializer):
    class Meta:
        model = TermsOfUse
        fields = ["pid", "title", "content", "created_at", "updated_at"]
