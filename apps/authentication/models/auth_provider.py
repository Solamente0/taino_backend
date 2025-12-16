from django.db import models

from base_utils.base_models import BaseModel


class AuthProvider(BaseModel):
    title = models.CharField(max_length=100)
    code = models.PositiveSmallIntegerField(default=0, db_index=True, null=True)
    redirect_uri = models.URLField(default=None, null=True)

    class Meta:
        verbose_name = "سرویس احراز هویت"
        verbose_name_plural = "سرویسهای احراز هویت"
