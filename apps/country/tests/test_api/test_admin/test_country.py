from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from apps.country.models import Country
from base_utils.base_tests import TainoBaseAdminAPITestCase


class CountryListTestAdminCase(TainoBaseAdminAPITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.country_count = 10
        self.countries = baker.make(Country, _quantity=self.country_count)
        self.url = reverse("country:country_admin:country-list")

    def test_list_countries(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), self.country_count)

    def test_unauthorized_admin_can_not_get_list_of_data(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CountryRetrieveTestAdminCase(TainoBaseAdminAPITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.country_name = "Tehran"
        self.country = baker.make(Country, name=self.country_name)
        self.url = reverse("country:country_admin:country-detail", args=[self.country.pid])

    def test_retrieve_country(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.country_name)


class CountryUpdateTestAdminCase(TainoBaseAdminAPITestCase):
    def setUp(self) -> None:
        super().setUp()

        self.country = baker.make(Country)
        self.url = reverse("country:country_admin:country-detail", args=[self.country.pid])

    def test_update_country_admin_successfully(self):
        data = {"is_sms_enabled": False}
        response = self.client.put(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["result"]["is_sms_enabled"], False)
