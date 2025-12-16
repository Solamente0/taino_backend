from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, CreatorModel, ActivableModel, AdminStatusModel

User = get_user_model()


class SMSTemplate(TimeStampModel, CreatorModel, ActivableModel):
    """
    Model to store SMS templates
    """

    TEMPLATE_TYPE_CHOICES = (
        ("court_session", _("یادآوری جلسه دادگاه")),
        ("objection_deadline", _("مهلت اعتراض")),
        ("exchange_deadline", _("مهلت تبادل لایحه")),
        ("other", _("سایر")),
    )

    name = models.CharField(max_length=100, verbose_name=_("نام قالب"))
    template_type = models.CharField(
        max_length=50, choices=TEMPLATE_TYPE_CHOICES, default="other", verbose_name=_("نوع قالب")
    )
    content = models.TextField(verbose_name=_("متن قالب"))
    is_system = models.BooleanField(default=False, verbose_name=_("قالب سیستمی"))

    class Meta:
        verbose_name = _("قالب پیامک")
        verbose_name_plural = _("قالب های پیامک")

    def __str__(self):
        return self.name
