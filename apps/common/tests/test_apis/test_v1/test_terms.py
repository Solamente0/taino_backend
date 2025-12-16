from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from apps.common.models import TermsOfUse
from base_utils.base_tests import TainoBaseAPITestCase


class TermsOfUseAPITest(TainoBaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.terms_count = 3
        self.terms = baker.make(
            TermsOfUse, title="Test Terms Title", content="Test Terms Content", is_active=True, _quantity=self.terms_count
        )
        # Create some inactive terms to test filtering
        self.inactive_terms = baker.make(
            TermsOfUse, title="Inactive Terms", content="Inactive Content", is_active=False, _quantity=2
        )

        self.url = reverse("common:common_v1:terms-of-use-list")

    def test_list_terms(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only active terms should be returned
        self.assertEqual(len(response.data), self.terms_count)

        # Check that inactive terms are not included
        for term in response.data:
            self.assertNotEqual(term["title"], "Inactive Terms")

    def test_retrieve_terms(self):
        term = self.terms[0]
        url = reverse("common:common_v1:terms-of-use-detail", args=[term.pid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], term.title)
        self.assertEqual(response.data["content"], term.content)

    def test_list_terms_without_login(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), self.terms_count)

    def test_search_terms(self):
        # Create a specific terms to search for
        specific_terms = baker.make(
            TermsOfUse, title="Specific Terms Title", content="Specific Terms Content", is_active=True
        )

        search_url = f"{self.url}?search=Specific"
        response = self.client.get(search_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Specific Terms Title")
