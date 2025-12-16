from django.db import models

from base_utils.base_models import CreatorModel, TimeStampModel, AdminStatusModel


class AppVersion(AdminStatusModel, CreatorModel, TimeStampModel):
    class UpdateStatus(models.TextChoices):
        NOT_UPDATED = "not_updated", "Not Updated"
        OPTIONAL_UPDATED = "optional_updated", "Optional Updated"
        FORCE_UPDATE = "force_update", "Force Update"

    class OSTypes(models.TextChoices):
        LINUX = "linux", "Linux"
        WINDOWS = "windows", "Windows"
        MAC = "mac", "Mac OS"
        ANDROID = "android", "Android"
        IOS = "ios", "iOS"
        PWA = "pwa", "PWA"
        WEB = "web", "Web"

    os = models.CharField(
        choices=OSTypes.choices,
        default=OSTypes.ANDROID,
        max_length=20,
        unique=False,
        db_index=True,
    )

    version_name = models.CharField(null=True, max_length=20)
    build_number = models.PositiveBigIntegerField(null=True)
    changelog = models.TextField(null=True, blank=True)

    update_status = models.CharField(choices=UpdateStatus.choices, default=UpdateStatus.NOT_UPDATED, max_length=20)

    icon = models.ForeignKey(
        to="document.TainoDocument",
        related_name="app_versions",
        on_delete=models.CASCADE,
        default=None,
        null=True,
    )

    @property
    def icon_url(self):
        return self.icon.url

    class Meta:
        unique_together = ("os", "build_number")
        verbose_name = "نسخه اپ"
        verbose_name_plural = "نسخ اپ"
