from celery import shared_task
from celery.utils.log import get_task_logger

from apps.messaging.services import MailManager
from apps.messaging.services.templates import TainoEmailTemplateSwitcherService

logger = get_task_logger(__name__)


@shared_task(bind=True)
def send_email_task(self, subject, to, html=None, plain_text=None, context=None):
    try:

        # MailManager().send(to_email=to, message=plain_text, title=subject)
        rendered_html = TainoEmailTemplateSwitcherService().render_template(
            template_name=context["template_code"],
            language=context["language_code"],
            template_context=context["context"],
        )
        MailManager().send_html_mail(to_email=to, rendered_html=rendered_html, title=subject)
        # simple_email_send(subject=subject, to=to, html=html, plain_text=plain_text)
    except Exception as exc:
        # https://docs.celeryq.dev/en/stable/userguide/tasks.html#retrying
        logger.warning(f"Exception occurred while sending email: {exc}")
        self.retry(exc=exc, countdown=5)
