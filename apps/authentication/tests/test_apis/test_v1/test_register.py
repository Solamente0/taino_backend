import uuid

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from apps.authentication.services import OTTGenerator
from apps.country.models import Country
from base_utils.base_tests import TainoBaseAPITestCase

User = get_user_model()


class RegisterTestCase(TainoBaseAPITestCase):
    def setUp(self):
        super().setUp()

        self.base_url = reverse("authentication:authentication_v1:authentication-register-api")
        self.new_phone_number = "9166672022"
        self.national_code = f"test_code_{uuid.uuid4().hex[:8]}"
        self.ir_country, _ = Country.objects.get_or_create(name="iran", code="IR", dial_code="98")
        self.first_name = self.faker.unique.first_name()
        self.last_name = self.faker.unique.last_name()
        self.email = self.faker.unique.email()
        self.otp = self.faker.unique.random_int(00000, 99999)

        self.new_pass = self.faker.password()
        self.client.logout()

    def generate_ott(self, phone_number):
        ott = OTTGenerator(
            # self.ir_country.dial_code +
            phone_number
        )
        ott.set_ott_to_cache()
        token = ott.get_ott_from_cache()
        return token

    def generate_ott_email(self, email):
        ott = OTTGenerator(email)
        ott.set_ott_to_cache()
        token = ott.get_ott_from_cache()
        return token

    def test_phone_number_register_success(self):
        token = self.generate_ott(self.new_phone_number)

        data = {
            "username": self.new_phone_number,
            "password": self.new_pass,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "country_alpha2": self.ir_country.code,
            "national_code": self.national_code,
            "lang_code": "fa",
            # "referral_code": str(self.faker.unique.random_int(00000, 99999)),
            "token": token,
        }

        response = self.client.post(self.base_url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.filter(phone_number__icontains=self.new_phone_number)
        self.assertTrue(user.exists(), "user does not exist in database")
        self.assertEquals(user.first().first_name, self.first_name)

    def test_email_register_success(self):
        token_email = self.generate_ott_email(self.email)

        data = {
            "username": self.email,
            "password": self.new_pass,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "national_code": self.national_code,
            "lang_code": "fa",
            "token": token_email,
        }

        response = self.client.post(self.base_url, data)
        self.assertTrue(
            response.status_code == 201,
            f"login failed: \nstatus code is: {response.status_code}\n response_data: {response}",
        )

        user = User.objects.filter(email__iexact=self.email)
        self.assertTrue(user.exists(), "user does not exist in database")
        self.assertEquals(user.first().first_name, self.first_name)

    def test_phone_number_token_invalid_failure(self):
        data = {
            "username": self.new_phone_number.replace("2", "5"),
            "password": self.new_pass,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "country_alpha2": self.ir_country.code,
            "national_code": self.national_code,
            "lang_code": "fa",
            # "referral_code": str(self.faker.unique.random_int(00000, 99999)),
            "token": self.faker.unique.first_name(),
        }

        response = self.client.post(self.base_url, data)
        self.assertTrue(
            response.status_code == status.HTTP_400_BAD_REQUEST,
        )

    def test_phone_number_username_already_exists_failure(self):
        token = self.generate_ott(self.user.phone_number)

        data = {
            "username": self.user.phone_number,
            "password": self.user_password,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "country_alpha2": self.ir_country.code,
            "national_code": self.national_code,
            "lang_code": "fa",
            # "referral_code": str(self.faker.unique.random_int(00000, 99999)),
            "token": token,
        }

        response = self.client.post(self.base_url, data)
        self.assertTrue(
            response.status_code == status.HTTP_400_BAD_REQUEST,
        )

    def test_registering_with_phone_number_sets_user_phone_country(self):
        token = self.generate_ott(self.new_phone_number)

        data = {
            "username": self.new_phone_number,
            "password": self.new_pass,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "country_alpha2": self.ir_country.code,
            "national_code": self.national_code,
            "lang_code": "fa",
            "token": token,
        }

        response = self.client.post(self.base_url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(phone_number=data["username"])
        self.assertEqual(user.phone_country.code, data["country_alpha2"])

    def test_registering_sets_user_default_country(self):
        token = self.generate_ott(self.new_phone_number)

        data = {
            "username": self.new_phone_number,
            "password": self.new_pass,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "country_alpha2": self.ir_country.code,
            "national_code": self.national_code,
            "default_country_code": self.ir_country.code,
            "lang_code": "fa",
            "token": token,
        }

        response = self.client.post(self.base_url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(phone_number=data["username"])
        self.assertEqual(user.country.code, data["default_country_code"])
