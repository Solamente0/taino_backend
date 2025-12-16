from django.db.models import QuerySet

from apps.document.models import TainoDocument
from base_utils.services import AbstractBaseQuery


class TainoDocumentQuery(AbstractBaseQuery):

    @staticmethod
    def get_visible_for_create_update(base_queryset: QuerySet[TainoDocument] = None) -> QuerySet[TainoDocument]:
        if not base_queryset:
            base_queryset = TainoDocument.objects.all()

        return base_queryset.filter(object_id=None)
