# apps/authentication/signals.py
import logging
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _

from apps.authentication.models import UserProfile

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=UserProfile)
def prevent_multiple_secretaries(sender, instance, **kwargs):
    """
    Signal to prevent a lawyer from having multiple secretaries
    """
    # Only check if this profile is a secretary being assigned to a lawyer
    if instance.is_secretary and instance.lawyer:
        # Check if the lawyer already has a secretary (not this one)
        existing_secretary = (
            UserProfile.objects.filter(lawyer=instance.lawyer, is_secretary=True).exclude(pk=instance.pk).first()
        )

        if existing_secretary:
            logger.warning(
                f"Attempted to assign secretary {instance.user.pid} to lawyer {instance.lawyer.pid} "
                f"who already has secretary {existing_secretary.user.pid}"
            )
            raise IntegrityError(_("This lawyer already has a secretary. Please remove the current secretary first."))
