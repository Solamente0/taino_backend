from django.urls import reverse
from rest_framework import status

from apps.authentication.services import OTTGenerator
from apps.country.models import Country
from base_utils.base_tests import TainoBaseAPITestCase


class ForgotPasswordTestCase(TainoBaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.base_url = reverse("authentication:authentication_v1:authentication-forgot-password-api")
        self.otp = self.faker.unique.random_int(00000, 99999)
        ott = OTTGenerator(self.user.phone_number)
        ott.set_ott_to_cache()
        self.token = ott.get_ott_from_cache()
        self.new_pass = self.faker.password()
        self.ir_country, _ = Country.objects.get_or_create(name="iran", code="IR", dial_code="98")

    def test_forgot_password_success(self):
        ott = OTTGenerator(self.user.phone_number)
        self.token = ott.get_ott_from_cache()
        data = {
            "token": self.token,
            "username": self.user.phone_number,
            "new_password": self.new_pass,
            "new_password_confirm": self.new_pass,
        }
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.base_url, data)
        self.assertTrue(
            response.status_code == 200,
            f"operation failed: \nstatus code is: {response.status_code}\n respnse_data: {response}",
        )

    def test_forgot_password_failure(self):
        response = self.client.post(self.base_url)
        self.assertTrue(
            response.status_code == 400,
            f"failed!\nstatus code is: {response.status_code}\n response_data: {response}",
        )

    def test_forgot_password_token_length_failure(self):
        data = {
            "token": self.token + "31414",
            "username": self.user.phone_number,
            "new_password": self.new_pass,
            "new_password_confirm": self.new_pass,
        }
        response = self.client.post(self.base_url, data)
        self.assertTrue(
            response.status_code == 400,
            f"failed!\nstatus code is: {response.status_code}\n response_data: {response}",
        )

    def test_forgot_password_new_password_confirm_failure(self):
        data = {
            "token": self.token,
            "username": self.user.phone_number,
            "new_password": self.new_pass,
            "new_password_confirm": self.new_pass + "3113d",
        }
        response = self.client.post(self.base_url, data)
        self.assertTrue(
            response.status_code == 400,
            f"failed!\nstatus code is: {response.status_code}\n response_data: {response}",
        )

    def test_forgot_password_username_failure(self):

        data = {
            "token": self.token,
            "username": self.faker.phone_number(),
            "country_alpha2": "IR",
            "new_password": self.new_pass,
            "new_password_confirm": self.new_pass,
        }
        response = self.client.post(self.base_url, data)
        self.assertTrue(
            response.status_code == status.HTTP_400_BAD_REQUEST,
        )
