from typing import List, Literal

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.core.files.uploadedfile import TemporaryUploadedFile, UploadedFile

from apps.document.models import TainoDocument
from base_utils.services import AbstractBaseService

User = get_user_model()


class DocumentService(AbstractBaseService):

    def __init__(self, instance: TainoDocument = None):
        self.instance = instance

    def set_instance(self, instance: TainoDocument):
        self.instance = instance

    def create_documents(
        self,
        creator: User,
        files: List[UploadedFile],
        content_type: ContentType,
        object_id: int = None,
        document_type=TainoDocument.DocumentTypeChoices.IMAGE.value,
    ) -> List[str]:
        uploaded_pid = []
        for f in files:
            doc = self.create_document(creator, f, content_type, object_id, document_type=document_type)
            uploaded_pid.append(doc.pid)

        return uploaded_pid

    def create_document(
        self,
        creator: User,
        file: UploadedFile,
        content_type: ContentType,
        object_id: int = None,
        document_type=TainoDocument.DocumentTypeChoices.IMAGE.value,
    ):
        import magic  # TODO: must be global

        mime_type = magic.from_buffer(file.read(), mime=True)
        file.seek(0)

        instance = TainoDocument.objects.create(
            file=File(file),
            creator=creator,
            content_type=content_type,
            object_id=object_id,
            document_type=document_type,
            mime_type=mime_type,
        )
        return instance

    def create_video(
        self, creator: User, file: TemporaryUploadedFile, content_type: ContentType, object_id: int = None
    ) -> TainoDocument:
        import magic  # TODO: must be global

        # Detect the mime type
        mime_type = magic.from_buffer(file.read(), mime=True)
        file.seek(0)

        instance = self.create_document(
            creator, file, content_type, object_id, document_type=TainoDocument.DocumentTypeChoices.VIDEO.value
        )
        instance.document_type = TainoDocument.DocumentTypeChoices.VIDEO.value
        instance.mime_type = mime_type  # Ensure mime_type is set
        instance.save()
        return instance

    def set_document_type(self, document_type: Literal[TainoDocument.DocumentTypeChoices.choices]):
        self.instance.document_type = document_type
        self.instance.save()

    def set_object_id(self, object_id: int):
        self.instance.object_id = object_id
        self.instance.save()
