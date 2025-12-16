from apps.common.models import FrequentlyAskedQuestion
from base_utils.serializers.base import TainoBaseModelSerializer


class FrequentlyAskedQuestionSerializer(TainoBaseModelSerializer):
    class Meta:
        model = FrequentlyAskedQuestion
        fields = ["pid", "question", "answer", "created_at", "updated_at"]
