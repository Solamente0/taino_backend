from django.db import models

from base_utils.base_models import TimeStampModel, DescriptiveModel


class ContactUs(TimeStampModel, DescriptiveModel):
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "تماس با ما"
        verbose_name_plural = "تماس با ما"
