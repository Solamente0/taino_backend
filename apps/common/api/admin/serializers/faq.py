from apps.common.models import FrequentlyAskedQuestion
from base_utils.serializers.base import TainoBaseModelSerializer


class FrequentlyAskedQuestionAdminSerializer(TainoBaseModelSerializer):
    class Meta:
        model = FrequentlyAskedQuestion
        fields = ["pid", "question", "answer", "order", "is_active", "created_at", "updated_at"]
        read_only_fields = ["pid", "created_at", "updated_at"]
