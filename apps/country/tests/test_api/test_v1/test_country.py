from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from apps.country.models import Country
from base_utils.base_tests import TainoBaseAPITestCase


class CountryTestCase(TainoBaseAPITestCase):

    def setUp(self) -> None:
        super().setUp()
        self.countries = baker.make(Country, _quantity=10)
        self.url = reverse("country:country_v1:country-list")

    def test_list_countries(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(self.countries))

    def test_unauthorized_user_can_get_list_of_data(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
