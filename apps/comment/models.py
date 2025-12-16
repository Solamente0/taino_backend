from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from apps.soft_delete.models import SoftDeleteModel
from base_utils.base_models import TimeStampModel, AdminStatusModel, AdminStatusChoices


class AbstractBaseComment(TimeStampModel, AdminStatusModel):
    admin_status = models.CharField(
        max_length=20, choices=AdminStatusChoices.choices, default=AdminStatusChoices.PENDING.value
    )

    body = models.TextField(max_length=500)

    rate = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        default=0,
    )

    is_pinned = models.BooleanField(default=False)
    has_bad_words = models.BooleanField(default=False)
    show_on_home_page = models.BooleanField(default=False)

    commenter = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="%(class)s_commenter", null=True, blank=True, db_index=True
    )
    parent = models.ForeignKey("self", on_delete=models.CASCADE, related_name="children", null=True, blank=True)

    class Meta:
        abstract = True
