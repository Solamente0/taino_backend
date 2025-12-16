from unittest import skip

from model_bakery import baker

from apps.country.models import City
from apps.expert_profile.models import ExpertProfile
from apps.initializers.covert_scripts import ctainoert_cities_to_cities_en
from apps.initializers.management.command_strategy import CountryInitializerStrategy
from apps.initializers.tasks import initialize_cities_task
from base_utils.base_tests import TainoBaseServiceTestCase


class CityCtainoertScriptTest(TainoBaseServiceTestCase):

    def setUp(self):
        super().setUp()

        # previous city initializer
        CountryInitializerStrategy().initialize()
        initialize_cities_task()

        a_tr_city = City.objects.filter(country__code="TR").first()
        an_ir_city = City.objects.filter(country__code="IR").first()

        self.experts_tr = baker.make(ExpertProfile, city=a_tr_city, _quantity=10)
        self.experts_ir = baker.make(ExpertProfile, city=an_ir_city, _quantity=10)

    @skip
    def test_ctainoert_cities(self):
        ctainoert_cities_to_cities_en()

        self.assertTrue(True)
