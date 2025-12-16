from django.contrib.auth import get_user_model
from django.db import models
from base_utils.base_models import TimeStampModel
from base_utils.randoms import generate_unique_public_id

User = get_user_model()


class ReferralLink(TimeStampModel):
    user = models.OneToOneField(
        to=get_user_model(), related_name="referral_links", on_delete=models.CASCADE, null=True, default=None
    )
    token = models.CharField(default=None, max_length=10, editable=False, unique=True)

    def save(self, *args, **kwargs):
        if not self.token:
            while True:
                # Generate a unique token (in this case, using UUID)
                token = generate_unique_public_id()[:6].upper()
                # Check if a model with the generated token already exists
                if not ReferralLink.objects.filter(token=token).exists():
                    self.token = token
                    break

        super(ReferralLink, self).save(*args, **kwargs)

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        If first_name or last_name is None, return an empty string.
        """
        first_name = self.user.first_name or ""
        last_name = self.user.last_name or ""
        full_name = f"{first_name} {last_name}".strip()
        return full_name if first_name or last_name else ""

    @property
    def link(self):
        return f"https://taino.ir/invite/{self.token}"

    class Meta:
        verbose_name = "لینک دعوت"
        verbose_name_plural = "لینکهای دعوت"
