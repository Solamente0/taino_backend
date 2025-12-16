from django.urls import reverse
from rest_framework import status

from base_utils.base_tests import TainoBaseAPITestCase


class APISwaggerTests(TainoBaseAPITestCase):
    """Test that ensures swagger launches successfully.
    It helps to prevent accepting merger requests that break swagger generation, by some errors in serializers or views.
    """

    def setUp(self) -> None:
        self.url = reverse("schema")

    def test_swagger_launches_successfully(self):

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
