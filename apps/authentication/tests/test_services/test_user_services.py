from unittest import skip

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.test import RequestFactory
from model_bakery import baker

from apps.authentication.services import UserService
from apps.authentication.services.auth import TainoAuthenticationBackend
from apps.country.models import Country
from apps.document.models import TainoDocument
from base_utils.base_tests import TainoBaseAPITestCase
from base_utils.validators import Validators

User = get_user_model()


class UserServicesTests(TainoBaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.password = "hellopass"
        self.ir_country, _ = Country.objects.get_or_create(name="Iran", code="IR", dial_code="98")
        self.lang = "fa"
        self.currency = "IRR"
        self.factory = RequestFactory()

    def test_user_change_password_success(self):
        user_repository = UserService()
        user_repository.set_user_password(self.user, self.password)
        self.assertTrue(check_password(self.password, self.user.password))

    def test_authentication_backend_success(self):
        user_repository = UserService()
        user_repository.set_user_password(self.user, self.password)
        self.client.force_authenticate(user=self.user)
        request = self.factory.get("/")
        request.user = self.user
        # request = self.client.get("/").wsgi_request
        # request.user = self.user
        back = TainoAuthenticationBackend()
        user = back.authenticate(request, self.user.phone_number, self.password)
        serialized_data = back.get_user_tokens_data(user)

        self.assertTrue(serialized_data.get("access_token"))
        self.assertTrue(serialized_data.get("refresh_token"))

    def test_user_repository_set_user_password_success(self):
        user_repository = UserService()
        user_repository.set_user_password(self.user, self.password)

        self.assertTrue(self.user.check_password(self.password))

    @skip
    def test_user_repository_concat_phone_number_success(self):
        user_repository = UserService()
        new_username = user_repository.concat_phone_number("9307605866", self.ir_country)
        self.assertTrue(str(new_username).startswith("98"))

    def test_user_repository_concat_phone_number_failure(self):
        user_repository = UserService()
        new_username = user_repository.concat_phone_number(self.faker.email(), self.ir_country)

        self.assertFalse(new_username.isdigit())
        self.assertTrue(Validators.is_email(new_username))

    def test_user_repository_check_username_failure(self):
        user_repository = UserService()
        new_username = user_repository.check_username(self.faker.unique.first_name())

        self.assertIsNone(new_username)

    def test_user_repository_get_user_by_username_success(self):
        user_repository = UserService()
        user = user_repository.get_user_by_username(self.user.phone_number)
        self.assertEquals(user, self.user)

    #
    # def test_user_repository_set_auth_provider_success(self):
    #     user_repository = UserService()
    #     result = user_repository.set_auth_provider(self.user, 1)
    #     self.assertTrue(result)
    #     self.assertEquals(self.user.auth_provider_id, self.auth_provider.id)
    #
    # #
    # def test_user_repository_set_user_currency_success(self):
    #     user_repository = UserService()
    #     result = user_repository.set_user_currency(self.user, "IRR")
    #     self.assertTrue(result)
    #     self.assertEquals(self.user.currency_id, self.currency.id)
