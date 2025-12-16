from apps.document.models import TainoDocument
from apps.document.services.document import DocumentService
from apps.social_media.models import SocialMediaType
from base_utils.services import AbstractBaseService


class SocialMediaTypeService(AbstractBaseService):

    def create_social_media(self, type: str, link: str, file: TainoDocument, is_active: bool = True):
        instance = SocialMediaType.objects.create(
            type=type,
            link=link,
            file=file,
            is_active=is_active,
        )
        DocumentService(file).set_object_id(instance.id)
        return instance
