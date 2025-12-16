from django.db import models

from base_utils.base_models import TimeStampModel, ActivableModel


class FrequentlyAskedQuestion(TimeStampModel, ActivableModel):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = "سوال متداول"
        verbose_name_plural = "سوالات متداول"
