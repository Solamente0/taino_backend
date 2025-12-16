from django.db.models import QuerySet

from apps.common.models import HomePage, FrequentlyAskedQuestion, TermsOfUse
from base_utils.services import AbstractBaseQuery


class FrequentlyAskedQuestionQuery(AbstractBaseQuery):
    @staticmethod
    def get_active_faqs(base_queryset: QuerySet[FrequentlyAskedQuestion] = None) -> QuerySet[FrequentlyAskedQuestion]:
        if not base_queryset:
            base_queryset = FrequentlyAskedQuestion.objects.all()

        return base_queryset.filter(is_active=True).order_by("order")
