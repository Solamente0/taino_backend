from typing import List

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import F, Q

from apps.soft_delete.models import SoftDeleteModel
from base_utils.randoms import generate_unique_public_id
from config.settings import AvailableLanguageChoices


class BaseModel(SoftDeleteModel):
    pid = models.CharField(unique=True, max_length=128)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["pid"]),
        ]

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self._state.adding or not self.pid:
            self.pid = generate_unique_public_id()
        super(BaseModel, self).save(force_insert=False, force_update=False, using=None, update_fields=None)


class TimeStampModel(BaseModel):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ActivableModel(BaseModel):
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class DescriptiveModel(BaseModel):
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(max_length=1000, null=True, blank=True)

    class Meta:
        abstract = True


class StaticalIdentifier(BaseModel):
    static_name = models.CharField(max_length=50, default=None, db_index=True, unique=True, null=True)

    class Meta:
        abstract = True


class BoundaryDateModel(models.Model):
    start_date = models.DateTimeField(default=None, null=True, blank=True)
    end_date = models.DateTimeField(default=None, null=True, blank=True)

    class Meta:
        abstract = True
        constraints = [models.CheckConstraint(name="start_date_before_end_date", check=Q(start_date__lt=F("end_date")))]

    def is_within_boundary(self, date):
        """Check if a given date is within the boundary dates."""
        return self.start_date <= date <= self.end_date

    def duration(self):
        """Get the duration between start_date and end_date."""
        return self.end_date - self.start_date

    #
    # def clean(self):
    #     """Ensure that start_date is before end_date."""
    #     if self.start_date >= self.end_date:
    #         raise ValidationError("start_date must be before end_date")


class AdminStatusChoices(models.TextChoices):
    NOT_SPECIFIED = "not_specified", "not_specified"
    ACTIVE = "active", "active"
    INACTIVE = "inactive", "inactive"
    VERIFIED = "verified", "verified"
    DRAFT = "draft", "draft"
    BANNED = "banned", "banned"
    CANCELED = "canceled", "canceled"
    PENDING = "pending", "pending"

    @classmethod
    def get_allowed_status_for_clients(cls) -> List[str]:
        return [cls.ACTIVE.value, cls.VERIFIED.value]


class AdminStatusModel(BaseModel):
    admin_status = models.CharField(
        max_length=20, choices=AdminStatusChoices.choices, default=AdminStatusChoices.ACTIVE.value
    )

    class Meta:
        abstract = True


class CreatorModel(BaseModel):
    creator = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE, related_name="%(class)s_creator")

    class Meta:
        abstract = True


# from django.contrib.gis.db import models as gis_model
# from django.contrib.postgres.indexes import GistIndex
# class PointLocationBaseModel(BaseModel):
#     point_location = gis_model.PointField(null=True)
#
#     class Meta:
#         abstract = True
#         indexes = [
#             GistIndex(fields=["point_location"]),
#         ]
