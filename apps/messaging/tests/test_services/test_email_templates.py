from apps.messaging.services.templates import TainoEmailTemplateSwitcherService, TainoEmailTemplate
from base_utils.base_tests import TainoBaseServiceTestCase
from config.settings import AvailableLanguageChoices


class EmailTemplateSwitchServiceTests(TainoBaseServiceTestCase):

    def setUp(self) -> None:
        self.template_switcher = TainoEmailTemplateSwitcherService()

    def test_email_template_switcher_based_on_langauge(self):
        rendered_template = self.template_switcher.render_template(
            TainoEmailTemplate.REGISTRATION,
            AvailableLanguageChoices.PERSIAN.value,
            {"code": 1234},
        )

        self.assertIsNotNone(rendered_template)

    def test_rendering_template_with_missing_context_keys_raise(self):
        with self.assertRaises(Exception) as e:
            self.template_switcher.render_template(
                TainoEmailTemplate.REGISTRATION, AvailableLanguageChoices.PERSIAN.value, template_context={}
            )

    def test_rendering_template_with_not_existing_template_name_raises_exception(self):
        with self.assertRaises(Exception) as e:
            self.template_switcher.render_template(
                "not_exising_name", AvailableLanguageChoices.PERSIAN.value, template_context={}
            )
