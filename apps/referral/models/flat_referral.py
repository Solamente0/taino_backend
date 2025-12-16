from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import CheckConstraint, Q, F
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from base_utils.base_models import TimeStampModel
from base_utils.randoms import generate_unique_public_id

User = get_user_model()


class FlatReferral(TimeStampModel):
    # class ReferralSourceChoices(models.TextChoices):
    #     DIRECT = "video", _("Video")
    #     AIRDROP = "airdrop", _("Airdrop")

    referrer = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="referrers")
    referred = models.OneToOneField(to=User, on_delete=models.CASCADE, related_name="referreds")
    is_claimed = models.BooleanField(default=False)
    value = models.FloatField(default=0.0)
    # source = models.CharField(choices=ReferralSourceChoices.choices)

    class Meta:
        unique_together = ("referrer", "referred")
        constraints = [
            CheckConstraint(
                check=~Q(referred=F("referrer")),
                name="check_referrer_and_referred_not_equal",
            ),
        ]
        verbose_name = "معرف ساده"
        verbose_name_plural = "معرفین ساده"

    def clean(self, *args, **kwargs):
        if self.referrer == self.referred:
            raise ValidationError(detail=_("The referrer can not be referred"))
