from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, CreatorModel, ActivableModel, AdminStatusModel

User = get_user_model()


class SystemSMSTemplate(TimeStampModel, ActivableModel):
    """
    System-defined SMS templates with placeholders
    """

    code = models.CharField(max_length=100, unique=True, verbose_name=_("کد قالب"))
    name = models.CharField(max_length=255, verbose_name=_("نام قالب"))
    template_content = models.TextField(verbose_name=_("متن قالب"))
    description = models.TextField(blank=True, null=True, verbose_name=_("توضیحات"))

    class Meta:
        verbose_name = _("قالب پیامک سیستمی")
        verbose_name_plural = _("قالب های پیامک سیستمی")

    def __str__(self):
        return self.name

    @classmethod
    def initialize_default_templates(cls):
        """Initialize default system templates"""
        defaults = [
            {
                "code": "court_session_reminder",
                "name": "یادآوری جلسه دادگاه",
                "template_content": "یاد آوری جلسه فردا {date} و ساعت {time} در {court_branch}. پرونده مربوط به {client_name}",
                "description": "قالب یادآوری جلسه دادگاه",
            },
            {
                "code": "objection_deadline_reminder",
                "name": "یادآوری مهلت اعتراض",
                "template_content": "سه روز مانده به پایان مهلت اعتراض به {objection_type} موضوع پرونده {case_subject} به نام {client_name}",
                "description": "قالب یادآوری مهلت اعتراض",
            },
            {
                "code": "exchange_deadline_reminder",
                "name": "یادآوری مهلت تبادل لایحه",
                "template_content": "سه روز مانده به پایان مهلت {exchange_type} موضوع پرونده {case_subject} به نام {client_name}",
                "description": "قالب یادآوری مهلت تبادل لایحه",
            },
        ]

        for template_data in defaults:
            cls.objects.update_or_create(
                code=template_data["code"],
                defaults={
                    "name": template_data["name"],
                    "template_content": template_data["template_content"],
                    "description": template_data["description"],
                    "is_active": True,
                },
            )
