from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from apps.common.models import HomePage, FrequentlyAskedQuestion, TermsOfUse
from base_utils.base_tests import TainoBaseAdminAPITestCase


class TermsOfUseAdminAPITest(TainoBaseAdminAPITestCase):
    def setUp(self):
        super().setUp()
        self.terms = baker.make(TermsOfUse, title="Test Terms Title", content="Test Terms Content", is_active=True)
        self.url = reverse("common:about_us_admin:terms-of-use-list")
        self.detail_url = reverse("common:about_us_admin:terms-of-use-detail", args=[self.terms.pid])

    def test_list_terms(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_terms(self):
        data = {"title": "New Terms Title", "content": "New Terms Content", "order": 1, "is_active": True}

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], data["title"])
        self.assertEqual(response.data["content"], data["content"])

    def test_update_terms(self):
        data = {"title": "Updated Terms Title", "content": "Updated Terms Content"}

        response = self.client.patch(self.detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], data["title"])
        self.assertEqual(response.data["content"], data["content"])
