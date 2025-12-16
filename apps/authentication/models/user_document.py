from django.db import models

from base_utils.base_models import AdminStatusModel, TimeStampModel
from base_utils.files import get_file_extension


class UserDocument(TimeStampModel, AdminStatusModel):

    class FileTypes(models.TextChoices):
        PDF = "pdf", "PDF"
        JPEG = "jpeg", "JPEG"
        JPG = "jpg", "JPG"
        PNG = "png", "PNG"
        DOCX = "docx", "DOCX"

    file_type = models.CharField(max_length=10, choices=FileTypes.choices, default=None, null=True)

    file = models.ForeignKey(
        to="document.TainoDocument",
        related_name="user_documents",
        on_delete=models.CASCADE,
        default=None,
        null=True,
    )

    creator = models.ForeignKey(
        to="TainoUser",
        on_delete=models.CASCADE,
        related_name="user_documents",
        default=None,
        null=True,
    )

    def set_file_type(self):
        if self.file.name in self.FileTypes.value:
            extension = get_file_extension(self.file)
            return extension.lower()

    @property
    def file_url(self):
        return self.file.url

    def save(self, *args, **kwargs):
        if not self.file_type:
            self.set_file_type()
        return super(UserDocument, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "سند کاربر سایت"
        verbose_name_plural = "اسناد کاربران سایت"
