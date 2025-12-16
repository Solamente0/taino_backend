from django.urls import reverse
from rest_framework import status

from apps.authentication.services import OTTGenerator
from base_utils.base_tests import TainoBaseAPITestCase


class EmailSetTestCase(TainoBaseAPITestCase):
    def setUp(self):
        super(EmailSetTestCase, self).setUp()
        self.base_url = reverse("authentication:authentication_v1:authentication-set-email-api")
        self.new_email = self.faker.email()
        ott = OTTGenerator(self.new_email)
        ott.set_ott_to_cache()
        self.token = ott.get_ott_from_cache()

    def test_set_email_success(self):
        data = {
            "username": self.new_email,
            "token": self.token,
        }

        response = self.client.post(self.base_url, data)

        # import pdb

        # pdb.set_trace()
        self.assertTrue(
            response.status_code == 200,
            f"operation failed: \nstatus code is: {response.status_code}\n respnse_data: {response}",
        )

    def test_send_email_failure(self):
        data = {
            "username": self.faker.email(),
            "token": self.token,
        }
        response = self.client.post(self.base_url, data)

        self.assertTrue(
            response.status_code == status.HTTP_400_BAD_REQUEST,
        )
