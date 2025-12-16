from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from apps.country.models import Country
from base_utils.base_tests import TainoBaseAPITestCase

User = get_user_model()


class LoginTestCase(TainoBaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.login_url = reverse("authentication:authentication_v1:authentication-login-api")
        self.ir_country, _ = Country.objects.get_or_create(name="iran", code="IR", dial_code="98")

        self.phone_login_data = {
            "username": self.user.phone_number,
            "password": self.user_password,
            "country_alpha2": self.ir_country.code,
        }

        self.email_login_data = {
            "username": self.user.email,
            "password": self.user_password,
        }

    def test_phone_number_login_success(self):
        self.client.logout()
        data = {
            "username": self.user.phone_number,
            "password": self.user_password,
            "country_alpha2": self.ir_country.code,
        }
        response = self.client.post(self.login_url, data)

        self.assertTrue(
            response.status_code == 200,
            f"login failed: \nstatus code is: {response.status_code}\n respnse_data: {response}",
        )

    def test_phone_number_login_user_not_found_failure(self):
        login_data = self.phone_login_data
        login_data["username"] = "9834314314"
        response = self.client.post(self.login_url, login_data)

        self.assertTrue(
            response.status_code == status.HTTP_400_BAD_REQUEST,
        )

    def test_email_login_success(self):
        response = self.client.post(self.login_url, data=self.email_login_data)
        self.assertTrue(
            response.status_code == 200,
            f"login failed with email: \nstatus code is: {response.status_code}\n respnse_data: {response}",
        )

    def test_phone_number_login_not_found_failure(self):
        wrong_login_data = {
            "username": self.faker.unique.random_int(9000000000, 9999999999),
            "password": self.faker.unique.random_int(111111111, 9999999999),
        }
        response = self.client.post(self.login_url, data=wrong_login_data)
        self.assertTrue(
            response.status_code == status.HTTP_400_BAD_REQUEST,
        )
