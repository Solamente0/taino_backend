from django.contrib.auth import get_user_model
from model_bakery import baker

from apps.country.models import Country, CountryTranslation
from apps.department.models import Department
from apps.finance.models import AssetPrice, Asset, AssetCategory
from apps.initializers.management.command_strategy import (
    CountryInitializerStrategy,
    LanguageInitializerStrategy,
    UserInitializerStrategy,
    DepartmentInitializerStrategy,
    SocialMediaTypeInitializerStrategy,
    GeneralSettingInitializerStrategy,
    CountryTranslationInitializerStrategy,
    FinanceInitializerStrategy,
)
from apps.language.models import Language
from apps.setting.models import GeneralSetting
from apps.social_media.models import SocialMediaType
from base_utils.base_tests import TainoBaseServiceTestCase


class CountryInitializerStrategyTests(TainoBaseServiceTestCase):

    def setUp(self) -> None:
        Country.global_objects.all().delete()

    def test_command_creates_counties(self):
        CountryInitializerStrategy().initialize()

        self.assertNotEqual(Country.objects.count(), 0)


class CountryTranslationInitializerStrategyTests(TainoBaseServiceTestCase):

    def setUp(self) -> None:
        Country.global_objects.all().delete()
        self.iran_country = baker.make(Country, code="IR")

    def test_command_creates_counties(self):
        CountryTranslationInitializerStrategy().initialize()

        self.assertNotEqual(CountryTranslation.objects.filter(main_object=self.iran_country).count(), 0)


class LanguageInitializerStrategyTests(TainoBaseServiceTestCase):

    def setUp(self) -> None:
        CountryInitializerStrategy().initialize()

    def test_command_creates_language(self):
        LanguageInitializerStrategy().initialize()

        self.assertNotEqual(Language.objects.count(), 0)


class UserInitializerStrategyTests(TainoBaseServiceTestCase):

    def setUp(self) -> None:
        pass

    def test_command_creates_user(self):
        UserInitializerStrategy().initialize()
        super_admin = get_user_model().objects.get(is_superuser=True)
        self.assertTrue(super_admin.password)


class DepartmentInitializerStrategyTests(TainoBaseServiceTestCase):

    def test_command_creates_departments(self):
        DepartmentInitializerStrategy().initialize()

        self.assertTrue(Department.objects.exists())


class SocialMediaTypeInitializerStrategyTests(TainoBaseServiceTestCase):

    def test_command_creates_social_media_type(self):
        SocialMediaTypeInitializerStrategy().initialize()
        self.assertTrue(SocialMediaType.objects.exists())


class GeneralSettingInitializerStrategyTests(TainoBaseServiceTestCase):

    def test_command_creates_admin_general_settings_type(self):
        GeneralSettingInitializerStrategy().initialize()
        self.assertTrue(GeneralSetting.objects.exists())


class FinanceInitializerStrategyTests(TainoBaseServiceTestCase):

    def test_command_finance_initializes_models(self):
        FinanceInitializerStrategy().initialize()
        self.assertTrue(Asset.objects.exists())
        self.assertTrue(AssetCategory.objects.exists())
        self.assertFalse(AssetPrice.objects.exists())  # will be filled by external API
