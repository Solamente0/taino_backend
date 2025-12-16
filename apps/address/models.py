from django.db import models

from base_utils.base_models import CreatorModel
from base_utils.base_models import TimeStampModel, DescriptiveModel


class Address(TimeStampModel, CreatorModel, DescriptiveModel):

    postal_code = models.CharField(max_length=15)
    country = models.ForeignKey(to="country.Country", on_delete=models.CASCADE, null=True, default=None)
    state = models.ForeignKey(to="country.State", on_delete=models.CASCADE, null=True, default=None)
    city = models.ForeignKey(to="country.City", on_delete=models.CASCADE, null=True, default=None)

    class Meta:
        verbose_name = "آدرس"
        verbose_name_plural = "آدرس ها"
