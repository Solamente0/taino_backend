from unittest import skip

from django.urls import reverse
from model_bakery import baker

from apps.address.models import Address
from apps.country.models import City, State, Country
from base_utils.base_tests import TainoBaseAPITestCase


@skip
class AdminUserAddressTestCase(TainoBaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.list_url = reverse("address:address_v1:user-address-api-list")
        self.post_url = reverse("address:address_v1:user-address-api-list")
        self.address_obj = baker.make(Address, _fill_optional=True, creator=self.user)
        self.country = baker.make(Country)
        self.state = baker.make(State)
        self.city = baker.make(City)
        self.all_address_objs = Address.objects.all()

    def test_user_address_success(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.list_url)

        self.assertTrue(response.status_code == 200)
        len_addresses = Address.objects.count()
        self.assertEqual(len(response.data), len_addresses)

    def test_user_address_retrieve_success(self):
        # dummy_data = {"pid": self.address_obj.pid}
        self.retrieve_url = reverse("address:address_v1:user-address-api-detail", kwargs={"pid": self.address_obj.pid})
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.retrieve_url)
        self.assertTrue(response.status_code == 200)
        self.assertEqual(response.data["first_name"], self.address_obj.first_name)

    def test_user_address_post_success(self):
        dummy_obj = baker.prepare(Address, _fill_optional=True)
        dummy_data = {
            "first_name": dummy_obj.first_name,
            "last_name": dummy_obj.last_name,
            "postal_code": dummy_obj.postal_code,
            "country": self.country.pid,
            "state": self.state.pid,
            "city": self.city.pid,
        }
        self.client.force_login(self.user)
        response = self.client.post(self.post_url, data=dummy_data)
        self.assertTrue(response.status_code == 201)
        self.assertEqual(response.data["last_name"], dummy_data["last_name"])

    def test_user_address_put_success(self):
        data = self.all_address_objs.last()
        self.put_url = reverse("address:address_v1:user-address-api-detail", kwargs={"pid": data.pid})
        dummy_data = baker.prepare(Address, _fill_optional=True)
        dummy_data = {
            "first_name": dummy_data.first_name,
            "last_name": dummy_data.last_name,
            "postal_code": dummy_data.postal_code,
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.put_url, data=dummy_data)
        self.assertTrue(response.status_code == 200)
        self.assertEqual(response.data["first_name"], dummy_data["first_name"])

    def test_user_address_patch_success(self):
        data = self.all_address_objs.last()
        self.patch_url = reverse("address:address_v1:user-address-api-detail", kwargs={"pid": data.pid})
        dummy_data = baker.prepare(Address, _fill_optional=True)
        dummy_data = {
            "first_name": dummy_data.first_name,
            "last_name": dummy_data.last_name,
            "postal_code": dummy_data.postal_code,
        }
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(self.patch_url, data=dummy_data)

        self.assertTrue(response.status_code == 200)
        self.assertEqual(response.data["first_name"], dummy_data["first_name"])

    # def test_user_address_delete_success(self):
    #     data = self.all_address_objs.last()
    #     self.delete_url = reverse("address:address_v1:user-address-api-detail", kwargs={"pid": data.pid})
    #
    #     dummy_data = model_to_dict(data)
    #     self.client.force_authenticate(user=self.user)
    #
    #     response = self.client.delete(self.post_url, data=dummy_data, content_type="application/json")
    #
    #     self.assertTrue(response.status_code == 204)
