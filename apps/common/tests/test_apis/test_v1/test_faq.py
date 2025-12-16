from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from apps.common.models import FrequentlyAskedQuestion
from base_utils.base_tests import TainoBaseAPITestCase


class FrequentlyAskedQuestionAPITest(TainoBaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.faq_count = 5
        self.faqs = baker.make(
            FrequentlyAskedQuestion, question="Test Question", answer="Test Answer", is_active=True, _quantity=self.faq_count
        )
        # Create some inactive FAQs to test filtering
        self.inactive_faqs = baker.make(
            FrequentlyAskedQuestion, question="Inactive Question", answer="Inactive Answer", is_active=False, _quantity=2
        )

        self.url = reverse("common:common_v1:frequently-questions-list")

    def test_list_faqs(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only active FAQs should be returned
        self.assertEqual(len(response.data), self.faq_count)

        # Check that inactive FAQs are not included
        for faq in response.data:
            self.assertNotEqual(faq["question"], "Inactive Question")

    def test_retrieve_faq(self):
        faq = self.faqs[0]
        url = reverse("common:common_v1:frequently-questions-detail", args=[faq.pid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["question"], faq.question)
        self.assertEqual(response.data["answer"], faq.answer)

    def test_list_faqs_without_login(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), self.faq_count)

    def test_search_faqs(self):
        # Create a specific FAQ to search for
        specific_faq = baker.make(
            FrequentlyAskedQuestion, question="Specific Question", answer="Specific Answer", is_active=True
        )

        search_url = f"{self.url}?search=Specific"
        response = self.client.get(search_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["question"], "Specific Question")
