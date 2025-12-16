from django.db import models
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import DescriptiveModel, StaticalIdentifier, ActivableModel


class UserType(ActivableModel, DescriptiveModel, StaticalIdentifier):
    color = models.CharField(max_length=6, null=True, blank=True)
    icon = models.ForeignKey(
        to="document.TainoDocument", related_name="user_type_icons", on_delete=models.CASCADE, default=None, null=True
    )

    def __str__(self):
        return f"{self.name or ''}"

    class Meta:
        verbose_name = "نقش کاربر"
        verbose_name_plural = "نقش های کاربری"
