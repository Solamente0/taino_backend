from django.db import models

from base_utils.base_models import CreatorModel, TimeStampModel, DescriptiveModel, ActivableModel


# class FeedBackCategory(CreatorModel, TimeStampModel, DescriptiveModel, ActivableModel):
#     """"""
#
#     code = models.IntegerField(_("code"), default=0, db_index=True)  # unique=True
#
#     # parent = models.ForeignKey(
#     #     to="self",
#     #     on_delete=models.CASCADE,
#     #     verbose_name=_("parent"),
#     #     null=True,
#     #     default=None,
#     #     blank=True,
#     # )


class FeedBack(CreatorModel, TimeStampModel):
    class FeedbackTypes(models.TextChoices):
        OK = "ok", "Ok"
        UNHAPPY = "unhappy", "Unhappy"
        SUGGESTED = "suggested", "Suggested"

    class FeedbackStatus(models.TextChoices):
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        PENDING = "pending", "Pending"

    feedback_type = models.TextField(choices=FeedbackTypes.choices, default=FeedbackTypes.OK)
    status = models.TextField(choices=FeedbackStatus.choices, default=FeedbackStatus.PENDING)
    message = models.TextField(max_length=1000, default="")

    class Meta:
        verbose_name = "بازخورد"
        verbose_name_plural = "بازخوردها"
