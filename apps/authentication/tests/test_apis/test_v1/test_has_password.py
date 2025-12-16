from django.contrib.auth import get_user_model
from django.urls import reverse

# from apps.common.models.ratelimit import RateLimitDefaultClass
from base_utils.base_tests import TainoBaseAPITestCase

User = get_user_model()


class HasPasswordTestCase(TainoBaseAPITestCase):

    def setUp(self):
        super().setUp()
        self.base_url = reverse("authentication:authentication_v1:authentication-has-password-api")
        self.user.set_password("pass")
        self.user.save()
        self.client.force_authenticate(user=self.user)

    def test_has_password_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.base_url)

        self.assertTrue(
            response.status_code == 200,
            f"operation failed: \nstatus code is: {response.status_code}\n respnse_data:{response.json()}",
        )

    def test_has_password_failure(self):
        # self.user = self.generateFakeData(User, password="fmieqpnqgpn", fill_all=True)
        self.user.set_unusable_password()
        self.user.save()
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.base_url)
        self.assertTrue(
            response.status_code == 200,
            f"failed!\nstatus code is: {response.status_code}\n response_data: {response.json()}",
        )
