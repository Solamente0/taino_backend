from django.db.models import QuerySet

from apps.common.models import HomePage, FrequentlyAskedQuestion, TermsOfUse
from base_utils.services import AbstractBaseQuery


class TermsOfUseQuery(AbstractBaseQuery):
    @staticmethod
    def get_active_terms(base_queryset: QuerySet[TermsOfUse] = None) -> QuerySet[TermsOfUse]:
        if not base_queryset:
            base_queryset = TermsOfUse.objects.all()

        return base_queryset.filter(is_active=True).order_by("order")
