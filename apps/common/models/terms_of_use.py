from django.db import models

from base_utils.base_models import TimeStampModel, ActivableModel


class TermsOfUse(TimeStampModel, ActivableModel):
    title = models.CharField(max_length=255)
    content = models.TextField()
    order = models.IntegerField(default=0)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, related_name="children", null=True, blank=True, default=None)

    class Meta:
        ordering = ["order"]
        verbose_name = "شرط استفاده"
        verbose_name_plural = "شرایط استفاده"
