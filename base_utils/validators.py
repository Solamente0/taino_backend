import re

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.authentication.services.regex import PHONE_NUMBER2
from base_utils.enums import AcceptedImageMimeType, AcceptedVideoMimeType, AcceptedDocumentMimeType


class Validators:

    @staticmethod
    def is_email(value: str) -> bool:
        try:
            validate_email(value)
            return True
        except Exception as e:
            return False

    @staticmethod
    def is_number(value: str) -> bool:
        try:
            return bool(re.match(PHONE_NUMBER2, value))
        except Exception as e:
            # log.info(f)
            return False

    @staticmethod
    def validate_image(file: UploadedFile):
        import magic  # TODO: must be global

        valid_mime_types = [mime_type for mime_type in AcceptedImageMimeType.values()]
        detected_mime_type = magic.from_buffer(file.read(), mime=True)
        file.seek(0)
        if detected_mime_type not in valid_mime_types:
            raise serializers.ValidationError(_("Unsupported image format"))

    @staticmethod
    def validate_video(file: UploadedFile):
        import magic  # TODO: must be global

        valid_mime_types = [mime_type for mime_type in AcceptedVideoMimeType.values()]
        detected_mime_type = magic.from_buffer(file.read(), mime=True)
        file.seek(0)
        if detected_mime_type not in valid_mime_types:
            raise serializers.ValidationError(_("Unsupported video format"))

    @staticmethod
    def validate_uploaded_image_size(file: UploadedFile):
        if file.size > settings.UPLOAD_API_MAX_IMAGE_SIZE:
            raise serializers.ValidationError(
                _(f"File size must be less than {settings.UPLOAD_API_MAX_IMAGE_SIZE/(1024*1024)} MB")
            )

    @staticmethod
    def validate_uploaded_video_size(file: UploadedFile):
        if file.size > settings.UPLOAD_API_MAX_VIDEO_SIZE:
            raise serializers.ValidationError(
                _(f"File size must be less than {settings.UPLOAD_API_MAX_VIDEO_SIZE/(1024*1024)} MB")
            )

    @staticmethod
    def validate_document(file: UploadedFile):
        import magic  # TODO: must be global

        valid_mime_types = [mime_type for mime_type in AcceptedDocumentMimeType.values()]
        detected_mime_type = magic.from_buffer(file.read(), mime=True)
        file.seek(0)
        if detected_mime_type not in valid_mime_types:
            raise serializers.ValidationError(_("Unsupported document format"))

    @staticmethod
    def validate_uploaded_document_size(file: UploadedFile):
        if file.size > settings.UPLOAD_API_MAX_DOCUMENT_SIZE:
            raise serializers.ValidationError(
                _(f"File size must be less than {settings.UPLOAD_API_MAX_DOCUMENT_SIZE/(1024*1024)} MB")
            )
