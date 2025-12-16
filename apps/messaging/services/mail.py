from django.conf import settings
from django.core import mail as django_mail
from django.core.mail import get_connection
from django.core.mail.backends.smtp import EmailBackend
from django.utils.safestring import SafeString


class MailManager:
    def __init__(self, connection: EmailBackend = None):
        self.connection = connection
        if self.connection is None:
            self.connection = get_connection(settings.EMAIL_BACKEND)

    def send(self, to_email: str, message: str, title: str, **kwargs) -> int:
        try:
            successes = django_mail.send_mail(
                subject=title,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[to_email],
                connection=self.connection,
                **kwargs,
            )
            return successes

        except Exception as e:
            # todo log
            pass

    def send_html_mail(self, to_email: str, title: str, rendered_html: SafeString):

        from django.core.mail import EmailMultiAlternatives

        message = EmailMultiAlternatives(
            connection=self.connection,
            subject=title,
            from_email=settings.EMAIL_HOST_USER,
            to=[to_email],
        )
        # message.mixed_subtype = "related"
        message.attach_alternative(rendered_html, "text/html")
        # message.attach(self.logo_data())

        message.send(fail_silently=False)

    def logo_data(self):
        from email.mime.image import MIMEImage

        with open(settings.BASE_DIR.joinpath("templates/email/assets/svg/logo.svg"), "rb") as f:
            logo_data = f.read()
        logo = MIMEImage(logo_data, _subtype="image/svg")
        logo.add_header("Content-ID", "<logo>")
        return logo
