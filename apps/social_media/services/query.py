from django.db.models import QuerySet

from apps.social_media.models import SocialMediaType
from base_utils.services import AbstractBaseQuery


class SocialMediaTypeQuery(AbstractBaseQuery):

    @staticmethod
    def get_visible_medias(base_queryset: QuerySet[SocialMediaType] = None) -> QuerySet[SocialMediaType]:
        if not base_queryset:
            base_queryset = SocialMediaType.objects.all()

        return base_queryset.filter(is_active=True)
