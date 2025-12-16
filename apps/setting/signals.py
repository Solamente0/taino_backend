from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.setting.models import GeneralSetting
from apps.setting.services.query import GeneralSettingsQuery


@receiver([post_save, post_delete], sender=GeneralSetting)
def invalidate_general_setting_cache(sender, instance, **kwargs):
    """Invalidate cache when a GeneralSetting is changed or deleted"""
    GeneralSettingsQuery._invalidate_cache(instance.key)
