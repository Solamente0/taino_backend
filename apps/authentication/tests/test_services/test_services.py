from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

from apps.authentication.services import UserService
from base_utils.base_tests import TainoBaseAPITestCase

User = get_user_model()


class AuthenticationServicesTests(TainoBaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.password = "hellopass"

    def test_user_change_password_success(self):
        user_repository = UserService()
        user_repository.set_user_password(self.user, self.password)
        self.assertTrue(check_password(self.password, self.user.password))

    # def test_authentication_backend_success(self):
    #     set_user_password(self.user, self.password)
    #     back = TainoAuthenticationBackend()
    #     back = back.authenticate(self.client.request(), self.user.username, self.password)
    #     serialized_data = back.get_user_tokens_data(self.user)
    #
    #     self.assertTrue(serialized_data.get("access_token"))
    #     self.assertTrue(serialized_data.get("refresh_token"))
