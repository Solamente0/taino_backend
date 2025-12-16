from unittest.mock import patch

from apps.country.models import Country, City
from apps.initializers.management.command_strategy import CountryInitializerStrategy
from apps.initializers.tasks import initialize_country_flags_task, initialize_cities_task
from base_utils.base_tests import TainoBaseServiceTestCase


class CountryFlagInitializer(TainoBaseServiceTestCase):

    def setUp(self) -> None:
        self.iran_country, _ = Country.objects.get_or_create(name="iran", code="IR", dial_code="98")

        self.file_mock_data = [
            {
                "model": "country.country",
                "pk": 101,
                "fields": {
                    "pid": "1319aa2d741b873bc019dc6e9ea2a204",
                    "created_at": "2024-03-15T09:40:50.876Z",
                    "updated_at": "2024-03-15T09:40:50.876Z",
                    "name": "Iran, Islamic Republic of",
                    "is_active": True,
                    "code": "IR",
                    "flag": "https://upload.wikimedia.org/wikipedia/commons/c/ca/Flag_of_Iran.svg",
                    "dial_code": "98",
                },
            },
        ]

    @patch("json.load")
    def test_update_country_flag(self, mock_load):
        mock_load.return_value = self.file_mock_data

        initialize_country_flags_task()
        self.iran_country = Country.objects.get(code="IR")
        self.assertIsNotNone(self.iran_country.flag)


class CityInitializerTests(TainoBaseServiceTestCase):

    def setUp(self) -> None:
        CountryInitializerStrategy().initialize()
        self.cities_api_response = {
            "error": False,
            "msg": "countries and cities retrieved",
            "data": [{"iso2": "IR", "iso3": "IRN", "country": "Iran", "cities": ["Tehran", "Yazd", "Shiraz"]}],
        }

    def test_command_creates_cities(self):

        initialize_cities_task()

        self.assertNotEqual(City.objects.count(), 0)
