from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from apps.country.models import City, State
from base_utils.base_tests import TainoBaseAdminAPITestCase


class CityListTestAdminCase(TainoBaseAdminAPITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.city_count = 10
        self.countries = baker.make(City, _quantity=self.city_count)
        self.url = reverse("country:country_admin:city-list")

    def test_list_cities(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), self.city_count)

    def test_unauthorized_admin_can_not_get_list_of_data(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CityRetrieveTestAdminCase(TainoBaseAdminAPITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.city_name = "Tehran"
        self.city = baker.make(City, name=self.city_name)
        self.url = reverse("country:country_admin:city-detail", args=[self.city.pid])

    def test_retrieve_city(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.city_name)


class CityUpdateTestAdminCase(TainoBaseAdminAPITestCase):
    def setUp(self) -> None:
        super().setUp()

        self.state = baker.make(State)
        self.another_state = baker.make(State, name="Karaj")
        self.city = baker.make(City, state=self.state)
        self.url = reverse("country:country_admin:city-detail", args=[self.city.pid])

    def test_update_city_admin_successfully(self):
        data = {"state": self.another_state.pid}
        response = self.client.put(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["state"], self.another_state.pid)
