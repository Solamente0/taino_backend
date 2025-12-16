from django.db.models import QuerySet

from apps.common.models import HomePage, FrequentlyAskedQuestion, TermsOfUse
from base_utils.services import AbstractBaseQuery


class HomePageQuery(AbstractBaseQuery):
    @staticmethod
    def get_active_homepage(base_queryset: QuerySet[HomePage] = None) -> QuerySet[HomePage]:
        if not base_queryset:
            base_queryset = HomePage.objects.all()

        return base_queryset.filter(is_active=True).order_by("-created_at")
