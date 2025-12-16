from django.db import models

from apps.document.models import TainoDocument
from base_utils.base_models import BaseModel, ActivableModel
from base_utils.base_models import TimeStampModel
from base_utils.base_models import TimeStampModel, DescriptiveModel
from base_utils.base_models import TimeStampModel, DescriptiveModel


class Country(ActivableModel, TimeStampModel, DescriptiveModel):
    description = None
    name = models.CharField(max_length=255, db_index=True, null=True)
    code = models.CharField(max_length=3, unique=True, db_index=True)
    flag = models.ForeignKey(TainoDocument, on_delete=models.SET_NULL, null=True)
    dial_code = models.CharField(
        max_length=5,
        null=True,
        db_index=True,
        # unique=True,
    )
    is_sms_enabled = models.BooleanField(default=False)

    class Meta:
        verbose_name = "کشور"
        verbose_name_plural = "کشورها"


class State(ActivableModel, TimeStampModel, DescriptiveModel):
    description = None
    name = models.CharField(max_length=255, db_index=True, null=True)
    pre_number = models.PositiveSmallIntegerField(null=True)
    country = models.ForeignKey(to="Country", related_name="states", on_delete=models.CASCADE, null=True)

    class Meta:
        verbose_name = "استان"
        verbose_name_plural = "استان ها"
        unique_together = ("name", "country")


class City(ActivableModel, TimeStampModel):
    description = None
    name = models.CharField(max_length=255, db_index=True, null=True)

    state = models.ForeignKey("State", related_name="cities", on_delete=models.CASCADE, null=True)
    country = models.ForeignKey(to=Country, on_delete=models.CASCADE, related_name="cities", null=True)

    class Meta:
        verbose_name = "شهر"
        verbose_name_plural = "شهرها"
        unique_together = ("name", "country", "state")
