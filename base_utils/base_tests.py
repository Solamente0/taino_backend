from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from faker import Faker
from model_bakery import baker
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken


class TainoBaseAPITestCase(APITestCase):
    @staticmethod
    def get_tokens_for_user(user):
        refresh = RefreshToken.for_user(user)
        return str(refresh), str(refresh.access_token)

    def setUp(self) -> None:
        self.default_header = {"Accept-Language": settings.LANGUAGE_CODE}
        self.client = APIClient(headers=self.default_header)
        self.faker = Faker()
        self.user_password = self.faker.password()
        self.user = baker.make(get_user_model(), email=self.faker.email(), phone_number="989374404910")
        self.user.set_password(self.user_password)
        self.user.save()

        self.admin_user = baker.make(get_user_model(), is_admin=True, is_superuser=True)
        self.client.force_login(self.user)


class TainoBaseAdminAPITestCase(TainoBaseAPITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user.is_admin = True
        self.user.save()


class TainoBaseServiceTestCase(TestCase):

    def setUp(self) -> None:
        self.faker = Faker()
        self.user_password = self.faker.password()
        self.user = baker.make(get_user_model(), email=self.faker.email(), phone_number="989374404910")
        self.user.set_password(self.user_password)
