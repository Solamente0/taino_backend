from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from base_utils.base_models import TimeStampModel, AdminStatusModel, DescriptiveModel, ActivableModel


class UserNotificationToken(TimeStampModel, AdminStatusModel):
    user = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE)
    token = models.CharField(max_length=1000, unique=True, blank=False, null=False)
    user_agent = models.CharField(max_length=1000, blank=True)


class UserSentNotification(TimeStampModel, DescriptiveModel, ActivableModel):
    link = models.CharField(max_length=500, null=True, blank=True)
    to_user = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE, db_index=True)
    seen = models.BooleanField(default=False, db_index=True)


class UserSentRequests(TimeStampModel, DescriptiveModel):

    class RequestTypeChoice(models.TextChoices):
        FOLLOW = "follow", "follow"
        COWORKER = "coworker", "coworker"
        AGENCY = "agency", "agency"

    request_type = models.CharField(choices=RequestTypeChoice.choices, db_index=True)

    from_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="from_requests")
    from_object_id = models.IntegerField()
    from_content_object = GenericForeignKey("from_content_type", "from_object_id")

    from_user = models.ForeignKey(
        to=get_user_model(), related_name="from_user_notifications", on_delete=models.CASCADE, db_index=True
    )
    to_user = models.ForeignKey(
        to=get_user_model(), related_name="to_user_notifications", on_delete=models.CASCADE, db_index=True
    )
    seen = models.BooleanField(default=False, db_index=True)
    is_done = models.BooleanField(default=False, db_index=True)
