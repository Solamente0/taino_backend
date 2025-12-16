from rest_framework import serializers

from apps.document.models import TainoDocument
from apps.document.services.document import DocumentService
from base_utils.enums import NamedContentTypeEnum, AcceptedDocumentMimeType, AcceptedImageMimeType, AcceptedVideoMimeType
from base_utils.serializers.base import TainoBaseSerializer
from base_utils.validators import Validators


class AdminImageUploadSerializer(TainoBaseSerializer):
    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())
    files = serializers.ListField(child=serializers.FileField(), write_only=True)
    file_type = serializers.ChoiceField(choices=NamedContentTypeEnum.labels, required=True, write_only=True)

    def validate_files(self, value):
        for file in value:
            Validators.validate_uploaded_image_size(file)
            Validators.validate_image(file)
        return value

    def create(self, validated_data):
        file_type = validated_data.get("file_type")
        creator = validated_data.get("creator")
        content_type = NamedContentTypeEnum.get_content_type_by_label(file_type)
        request_files = validated_data.get("files", [])
        # request_files = self.context["request"].FILES.getlist("files")

        uploaded_pid = DocumentService().create_documents(
            creator=creator,
            files=request_files,
            content_type=content_type,
        )

        return uploaded_pid

    def to_representation(self, instance):
        data = {"pid": instance}
        return data


class AdminVideoUploadSerializer(TainoBaseSerializer):
    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())
    file = serializers.FileField()
    file_type = serializers.ChoiceField(choices=NamedContentTypeEnum.labels, required=True, write_only=True)

    def validate_file(self, value):
        Validators.validate_uploaded_video_size(value)
        Validators.validate_video(value)
        return value

    def create(self, validated_data):
        file_type = validated_data.get("file_type")
        content_type = NamedContentTypeEnum.get_content_type_by_label(file_type)
        creator = validated_data["creator"]
        file = validated_data["file"]

        # request_files = self.context["request"].FILES.getlist("file")[0]

        repository = DocumentService()
        instance = repository.create_video(
            creator=creator,
            file=file,
            content_type=content_type,
        )
        return instance.pid

    def to_representation(self, instance):
        data = {"pid": instance}
        return data


# apps/document/api/admin/serializers.py
class AdminDocumentUploadSerializer(TainoBaseSerializer):
    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())
    files = serializers.ListField(child=serializers.FileField(), write_only=True)
    file_type = serializers.ChoiceField(choices=NamedContentTypeEnum.labels, required=True, write_only=True)

    def validate_files(self, value):
        for file in value:
            Validators.validate_uploaded_document_size(file)
            Validators.validate_document(file)
        return value

    def create(self, validated_data):
        file_type = validated_data.get("file_type")
        creator = validated_data.get("creator")
        content_type = NamedContentTypeEnum.get_content_type_by_label(file_type)
        request_files = validated_data.get("files", [])

        document_type = self._get_document_type_from_files(request_files)

        uploaded_pid = DocumentService().create_documents(
            creator=creator, files=request_files, content_type=content_type, document_type=document_type
        )

        return uploaded_pid

    def _get_document_type_from_files(self, files):
        if not files:
            return TainoDocument.DocumentTypeChoices.PDF.value

        import magic  # TODO: must be global

        file = files[0]
        mime_type = magic.from_buffer(file.read(), mime=True)
        file.seek(0)

        # Store the detected mime type for later use when creating the document
        self.detected_mime_type = mime_type

        if mime_type == AcceptedDocumentMimeType.PDF.value:
            return TainoDocument.DocumentTypeChoices.PDF.value
        elif mime_type in [AcceptedDocumentMimeType.DOCX.value, AcceptedDocumentMimeType.DOC.value]:
            return TainoDocument.DocumentTypeChoices.DOCX.value
        elif mime_type == AcceptedDocumentMimeType.TXT.value:
            return TainoDocument.DocumentTypeChoices.TXT.value
        elif mime_type in [m.value for m in AcceptedImageMimeType]:
            return TainoDocument.DocumentTypeChoices.IMAGE.value
        elif mime_type in [m.value for m in AcceptedVideoMimeType]:
            return TainoDocument.DocumentTypeChoices.VIDEO.value

        return TainoDocument.DocumentTypeChoices.PDF.value

    def to_representation(self, instance):
        data = {"pid": instance}
        return data
