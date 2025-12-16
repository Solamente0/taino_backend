from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from base_utils.base_models import TimeStampModel, DescriptiveModel, CreatorModel


def document_upload_to(document_instance, filename) -> str:
    return f"{document_instance.content_type.app_label}/{document_instance.content_type.model}/{document_instance.pid + '-' + filename}"


class TainoDocument(TimeStampModel, DescriptiveModel, CreatorModel):
    class DocumentTypeChoices(models.TextChoices):
        IMAGE = "image"
        VIDEO = "video"
        PDF = "pdf"
        DOCX = "docx"
        TXT = "txt"

    creator = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE, related_name="documents", null=True)
    document_type = models.CharField(choices=DocumentTypeChoices.choices, max_length=15, default=DocumentTypeChoices.IMAGE)
    file = models.FileField(upload_to=document_upload_to)
    mime_type = models.CharField(max_length=100, null=True, blank=True)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, db_index=True, default=None, null=True, blank=True
    )
    object_id = models.IntegerField(db_index=True, null=True, blank=True)
    content_object = GenericForeignKey()

    is_public = models.BooleanField(default=False)

    @property
    def url(self) -> str:
        if settings.USE_AWS_S3:
            return self.file.url
        # todo a better idea would be customizing file field of  DRF
        # todo separate admin route v1 route
        return "/api/document/v1/{}/download/".format(self.pid)

    def __str__(self):
        if self.name:
            return f"Document: {self.name} id: {self.pk}"
        else:
            return f"File Name: {self.file.name}"

    def save(self, *args, **kwargs):
        # self.change_dynamic_storage()
        super().save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # self.change_dynamic_storage()

    # def change_dynamic_storage(self):
    #     if settings.USE_AWS_S3:
    # from config.settings import EtlVideoS3Storage, TainoBusinessProfileS3Storage
    #
    # if self.document_type == self.DocumentTypeChoices.VIDEO.value:
    #     storage = EtlVideoS3Storage()
    # else:
    #     storage = TainoBusinessProfileS3Storage()

    # self.file.storage = storage

    class Meta:
        verbose_name = "سند"
        verbose_name_plural = "اسناد"
