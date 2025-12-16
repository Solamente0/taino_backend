from django.db import models
from django.utils.crypto import get_random_string

from base_utils.base_models import TimeStampModel, ActivableModel


class Newsletter(TimeStampModel, ActivableModel):
    email = models.EmailField(unique=True)
    unsubscribe_token = models.CharField(max_length=50, unique=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "عضو خبرنامه"
        verbose_name_plural = "عضوهای خبرنامه"

    def save(self, *args, **kwargs):
        if not self.unsubscribe_token:
            self.unsubscribe_token = get_random_string(length=40)
        super().save(*args, **kwargs)
