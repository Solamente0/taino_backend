from apps.setting.models import GeneralSetting, GeneralSettingChoices
from apps.setting.services.query import GeneralSettingsQuery
from base_utils.base_tests import TainoBaseServiceTestCase


class GeneralSettingsQueryTests(TainoBaseServiceTestCase):

    def setUp(self) -> None:
        self.faq_setting = GeneralSetting.objects.get_or_create(key=GeneralSettingChoices.HELP_CENTER_FAQ.value)
        self.term_setting = GeneralSetting.objects.get_or_create(key=GeneralSettingChoices.HELP_CENTER_TERMS.value)

    def test_get_visible_real_estate_projects_not_giving_inactive_objects(self):
        settings = GeneralSettingsQuery.get_visible_mobile_settings()

        self.assertEqual(settings.count(), 2)
