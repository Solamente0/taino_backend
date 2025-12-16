from django.core.validators import FileExtensionValidator
from django.db import models

from base_utils.base_models import TimeStampModel, ActivableModel


class AboutUs(TimeStampModel, ActivableModel):
    title = models.CharField(max_length=128, default=None, null=True, blank=True)
    history = models.TextField(default=None, null=True, blank=True)
    values = models.TextField(default=None, null=True, blank=True)
    services = models.TextField(default=None, null=True, blank=True)
    team_description = models.TextField(default=None, null=True, blank=True)
    extra = models.TextField(default=None, null=True, blank=True)

    class Meta:
        verbose_name = "درباره ما"
        verbose_name_plural = "درباره ما"


class AboutUsTeamMember(TimeStampModel, ActivableModel):
    full_name = models.CharField(max_length=255)
    job_title = models.CharField(max_length=30)
    resume_link = models.URLField(max_length=500, default=None, null=True, blank=True)
    avatar = models.ForeignKey(
        "document.TainoDocument", on_delete=models.SET_NULL, related_name="team_member_avatars", null=True, blank=True
    )
    about_us = models.ForeignKey(
        to="AboutUs", related_name="team_members", on_delete=models.CASCADE, default=None, null=True, blank=True
    )
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "عضو تیم (صفحه درباره ما)"
        verbose_name_plural = "اعضای تیم (صفحه درباره ما)"
        ordering = ["order"]
