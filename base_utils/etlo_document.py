import requests
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile

from apps.document.models import TainoDocument


def save_document_from_url(url, content_object, document_type='image', is_public=False):
    response = requests.get(url)
    if response.status_code == 200:
        file_name = url.split('/')[-1]
        file_content = ContentFile(response.content, name=file_name)

        content_type = ContentType.objects.get_for_model(content_object)

        document = TainoDocument(
            document_type=document_type,
            file=file_content,
            content_type=content_type,
            object_id=content_object.id,
            is_public=is_public
        )
        document.save()
        return document
    else:
        raise Exception(f"Failed to download file from URL: {url}")
