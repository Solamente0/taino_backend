from unittest import skip

from django.urls import reverse

from apps.authentication.services import OTPGenerator
from apps.authentication.services.validators import check_and_repair_username
from apps.country.models import Country
from base_utils.base_tests import TainoBaseAPITestCase


class OTPTestCase(TainoBaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.base_url = reverse("authentication:authentication_v1:authentication-send-otp-api")
        self.verify_base_url = reverse("authentication:authentication_v1:authentication-verify-otp-api")

        self.new_phone_number = "9374404910"
        self.email = self.faker.email()
        self.ir_country, _ = Country.objects.get_or_create(name="iran", code="IR", dial_code="98")
        self.user_identifier = check_and_repair_username(self.new_phone_number, self.ir_country)
        self.user_template = f"user-{self.user_identifier}-otp"
        self.otp_generator = OTPGenerator(self.user_identifier)
        self.otp_username = self.user_identifier

    def test_phone_number_otp_send_success(self):
        data = {
            "username": self.new_phone_number,
            "country_alpha2": self.ir_country.code,
        }
        response = self.client.post(self.base_url, data)

        self.assertTrue(
            response.status_code == 200,
            f"operation failed: \nstatus code is: {response.status_code}\n respnse_data: {response}",
        )
        self.otp_code = self.otp_generator.get_otp_from_cache()
        self.assertIsNotNone(self.otp_code, "OTP Not set")

    def test_email_otp_send_success(self):
        data = {
            "username": self.email,
        }
        response = self.client.post(self.base_url, data)
        self.assertTrue(
            response.status_code == 200,
            f"operation failed: \nstatus code is: {response.status_code}\n respnse_data: {response}",
        )

    @skip
    def test_otp_verify_success(self):
        otp_generator = OTPGenerator(self.user_identifier)
        is_sent, time_remaining = otp_generator.send_code()
        otp_code = self.otp_generator.get_otp_from_cache()

        data = {
            "username": self.new_phone_number,
            "country_alpha2": self.ir_country.code,
            "otp": otp_code,
        }
        otp_validator = OTPGenerator(user_identifier=self.user_identifier, otp=otp_code)

        response = self.client.post(self.verify_base_url, data)

        self.assertTrue(
            response.status_code == 202,
            f"operation failed: \nstatus code is: {response.status_code}\n respnse_data: {response}",
        )

    def test_otp_send_failure(self):
        data = {
            "username": "31r13fvk13t9",
        }
        response = self.client.post(self.base_url, data)

        self.assertTrue(
            response.status_code == 400,
            f"failed!\nstatus code is: {response.status_code}\n response_data: {response}",
        )

    def test_otp_verify_failure(self):
        self.otp_generator.set_otp_to_cache()
        self.otp_code = self.otp_generator.get_otp_from_cache()

        data = {
            "username": self.user_identifier,
            "country_alpha2": self.ir_country.code,
            "otp": str(self.otp_code) + "6",
        }
        response = self.client.post(self.verify_base_url, data)
        self.assertTrue(
            response.status_code == 400,
            f"failed!\nstatus code is: {response.status_code}\n response_data: {response}",
        )
