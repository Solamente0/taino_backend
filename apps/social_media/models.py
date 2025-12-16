from django.db import models

from apps.document.models import TainoDocument
from base_utils.base_models import BaseModel, ActivableModel, TimeStampModel


class SocialMediaType(ActivableModel, TimeStampModel):
    type = models.CharField(max_length=50, unique=True)
    link = models.CharField(max_length=500)
    file = models.ForeignKey(TainoDocument, on_delete=models.CASCADE, null=True)

    class Meta:
        verbose_name = "نوع شبکه اجتماعی"
        verbose_name_plural = "انواع شبکه های اجتماعی"
