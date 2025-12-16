from django.contrib.auth import get_user_model
from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from base_utils.base_tests import TainoBaseAPITestCase

User = get_user_model()


class AdminLoginTestCase(TainoBaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.login_url = reverse("authentication:auth_admin:token_obtain_pair")
        self.refresh_url = reverse("authentication:auth_admin:token_refresh")
        self.user.is_admin = True
        self.user.save()

        self.user1 = baker.make(get_user_model(), email=self.faker.email(), phone_number="989307605866")
        self.user1.set_password(self.user_password)
        self.user1.is_admin = False
        self.user1.save()

        self.admin_login_data = {
            "username": self.user.phone_number,
            "password": self.user_password,
        }

    def test_admin_login_success(self):
        self.client.logout()
        response = self.client.post(self.login_url, self.admin_login_data)
        self.assertTrue(response.status_code == status.HTTP_200_OK)

    def test_admin_login_user_not_is_staff_failure(self):
        self.client.logout()

        login_data = {
            "username": self.user1.phone_number,
            "password": self.user_password,
        }

        response = self.client.post(self.login_url, login_data)

        self.assertTrue(response.status_code == status.HTTP_403_FORBIDDEN)

    def test_admin_login_not_found_failure(self):
        self.client.logout()
        wrong_login_data = {
            "username": self.faker.unique.random_int(9000000000, 9999999999),
            "password": self.faker.unique.random_int(111111111, 9999999999),
        }
        response = self.client.post(self.login_url, data=wrong_login_data)
        self.assertTrue(response.status_code == status.HTTP_403_FORBIDDEN)

    def test_admin_refresh_success(self):
        self.client.logout()
        refresh, access = self.get_tokens_for_user(self.user)
        refresh_data = {"refresh": refresh}

        response = self.client.post(self.refresh_url, refresh_data)
        self.assertTrue(response.status_code == status.HTTP_200_OK)
        self.assertNotEqual(response.data["refresh_token"], refresh)  # for rotating refresh token
