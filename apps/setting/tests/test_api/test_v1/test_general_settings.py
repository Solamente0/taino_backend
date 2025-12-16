from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from apps.setting.models import GeneralSetting, GeneralSettingChoices
from base_utils.base_tests import TainoBaseAPITestCase


class GeneralSettingsTests(TainoBaseAPITestCase):

    def setUp(self) -> None:
        super().setUp()
        self.faq_setting = GeneralSetting.objects.get_or_create(key=GeneralSettingChoices.HELP_CENTER_FAQ.value)
        self.term_setting = GeneralSetting.objects.get_or_create(key=GeneralSettingChoices.HELP_CENTER_TERMS.value)

        baker.make(GeneralSetting, key=GeneralSettingChoices.BUSINESS_PROFILE_COWORKER_FREE_LIMIT.value)
        baker.make(GeneralSetting, key=GeneralSettingChoices.BUSINESS_PROFILE_COWORKER_PRO_LIMIT.value)

        self.url = reverse("setting:setting_v1:general-list")

    def test_list_general_settings_successfully(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_general_settings_without_being_login_fails(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
