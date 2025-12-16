from django.core.management import call_command

from apps.country.models import Country, CountryTranslation
from apps.department.models import Department
from apps.language.models import Language
from apps.setting.models import GeneralSetting
from apps.social_media.models import SocialMediaType
from base_utils.base_tests import TainoBaseServiceTestCase


# todo fix it, takes so much time to run the test
# TODO: fix race condition for country objects!
class CountryInitializerStrategyTests(TainoBaseServiceTestCase):
    def setUp(self) -> None: ...

    def test_command_runs_successfuly(self):
        call_command("initialize")
        self.assertTrue(True)

        self.assertNotEqual(Country.objects.count(), 0)
        self.assertNotEqual(CountryTranslation.objects.count(), 0)
        self.assertNotEqual(Language.objects.count(), 0)
        self.assertTrue(Department.objects.exists())
        self.assertTrue(SocialMediaType.objects.exists())
        self.assertTrue(GeneralSetting.objects.exists())
