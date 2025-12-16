from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from apps.country.models import City
from base_utils.base_tests import TainoBaseAPITestCase


class CityTestCase(TainoBaseAPITestCase):

    def setUp(self) -> None:
        super().setUp()
        self.cities = baker.make(City, _quantity=10)
        self.url = reverse("country:country_v1:city-list")

    def test_list_cities(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(self.cities))

    def test_unauthorized_user_can_not_get_list_of_data(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(self.cities))
