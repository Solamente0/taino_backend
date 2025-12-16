from django.conf import settings
from apps.document.models import TainoDocument


def get_document_download_file(document_pid: str):
    if settings.USE_AWS_S3:
        raise Exception("Service Not Available")

    try:
        document = TainoDocument.objects.get(pid=document_pid)
        return document.file.file, document.mime_type

    except Exception as e:
        raise Exception
