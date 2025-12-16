from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from apps.country.models import State, Country
from base_utils.base_tests import TainoBaseAdminAPITestCase


class StateListTestAdminCase(TainoBaseAdminAPITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.state_count = 10
        self.countries = baker.make(State, _quantity=self.state_count)
        self.url = reverse("country:country_admin:state-list")

    def test_list_states(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), self.state_count)

    def test_unauthorized_admin_can_not_get_list_of_data(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class StateRetrieveTestAdminCase(TainoBaseAdminAPITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.state_name = "Tehran"
        self.state = baker.make(State, name=self.state_name)
        self.url = reverse("country:country_admin:state-detail", args=[self.state.pid])

    def test_retrieve_state(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.state_name)


class StateUpdateTestAdminCase(TainoBaseAdminAPITestCase):
    def setUp(self) -> None:
        super().setUp()

        self.country = baker.make(Country)
        self.another_country = baker.make(Country, name="Karaj")
        self.state = baker.make(State, country=self.country)
        self.url = reverse("country:country_admin:state-detail", args=[self.state.pid])

    def test_update_state_admin_successfully(self):
        data = {"country": self.another_country.pid}
        response = self.client.put(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["country"], self.another_country.pid)
