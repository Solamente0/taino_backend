from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from apps.country.models import Country
from apps.document.models import TainoDocument
from base_utils.base_tests import TainoBaseAPITestCase


class UserProfileAPITestCase(TainoBaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user.avatar = baker.make(TainoDocument)
        self.user.save()

        self.country = baker.make(Country, is_sms_enabled=True)

        self.url = reverse("user:user_v1:user_profile-profile")

    def test_get_user_profile(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_profile(self):

        data = {
            "first_name": "changed name",
            "country": self.country.code,
            "currency": "IR",
        }
        response = self.client.patch(self.url, data)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.country.code, data["country"])
        self.assertEqual(self.user.currency.currency_code, data["currency"])
        self.assertEqual(self.user.first_name, data["first_name"])
