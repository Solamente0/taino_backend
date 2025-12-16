from unittest import skip

from django.core.mail import get_connection
from django.test import SimpleTestCase

from apps.messaging.services import IranSmsManager, MailManager
from apps.messaging.services.templates import TainoEmailTemplateSwitcherService, TainoEmailTemplate
from config.settings import AvailableLanguageChoices


class MailManagerTest(SimpleTestCase):

    def setUp(self):
        self.smtp_manager = MailManager(get_connection("django.core.mail.backends.smtp.EmailBackend"))
        self.in_memory_manager = MailManager(get_connection("django.core.mail.backends.locmem.EmailBackend"))

    def test_sending_simple_text_mail(self):
        self.in_memory_manager.send(
            "mh.chris2014@gmail.com",
            "This is a test mail for testing smtp configuration in django",
            "Mail test title",
        )

        self.assertTrue(True)

    def test_sending_html_mail(self):
        rendered_template = TainoEmailTemplateSwitcherService().render_template(
            TainoEmailTemplate.REGISTRATION,
            AvailableLanguageChoices.PERSIAN.value,
            {"code": 1234},
        )
        self.in_memory_manager.send_html_mail(
            "mh.chris2014@gmail.com",
            "test",
            rendered_template,
        )

        self.assertTrue(True)


class IranSmsManagerTest(SimpleTestCase):

    @skip
    def test_sending_verification_code_successfully(self):
        manager = IranSmsManager()
        # manager.send("09374404910", "متن تست")
        manager.send_verification_code("9374404910", "1234")
        self.assertTrue(True)
