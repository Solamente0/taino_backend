from django.contrib.auth import get_user_model
from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from apps.country.models import Country
from apps.document.models import TainoDocument
from base_utils.base_tests import TainoBaseAPITestCase

User = get_user_model()


class CreateUserAdminAPITests(TainoBaseAPITestCase):

    def setUp(self) -> None:
        super().setUp()
        self.user.is_admin = True
        self.user.save()

        self.country = baker.make(Country)
        self.avatar = baker.make(TainoDocument)

        self.url = reverse("user:user_admin:admin_users-list")

    def test_create_user_successfully(self):
        data = {
            "avatar": self.avatar.pid,
            "first_name": "Ali",
            "last_name": "Alavi",
            "phone_number": "9374425845",
            "phone_country": self.country.pid,
            "email": "test@test.com",
            "is_active": True,
            "has_premium_account": False,
            "is_email_verified": False,
            "is_phone_number_verified": True,
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=data["email"])
        self.assertEquals(data["phone_country"], user.phone_country.pid)

    def test_create_user_sets_user_default_country(self):
        data = {
            "avatar": self.avatar.pid,
            "first_name": "Ali",
            "last_name": "Alavi",
            "phone_number": "9374425845",
            "phone_country": self.country.pid,
            "country": self.country.pid,
            "email": "test@test.com",
            "is_active": True,
            "has_premium_account": False,
            "is_email_verified": False,
            "is_phone_number_verified": True,
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=data["email"])
        self.assertEquals(data["country"], user.country.pid)


class UpdateUserAdminAPITests(TainoBaseAPITestCase):

    def setUp(self) -> None:
        super().setUp()
        self.user.is_admin = True
        self.user.save()

        self.country = baker.make(Country)
        self.avatar = baker.make(TainoDocument)
        self.user_to_update = baker.make(get_user_model())

        self.url = reverse("user:user_admin:admin_users-detail", args=[self.user_to_update.pid])

    def test_update_user_successfully(self):
        data = {
            "first_name": "Ali",
            "phone_country": self.country.pid,
            "country": self.country.pid,
            "avatar": self.avatar.pid,
        }

        response = self.client.patch(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user_to_update.refresh_from_db()
        self.assertEquals(data["phone_country"], self.user_to_update.phone_country.pid)
        self.assertEquals(data["country"], self.user_to_update.country.pid)
        self.assertEquals(data["avatar"], self.user_to_update.avatar.pid)
        self.assertEquals(data["first_name"], self.user_to_update.first_name)
