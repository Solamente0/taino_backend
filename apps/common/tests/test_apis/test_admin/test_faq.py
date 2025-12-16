from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from apps.common.models import HomePage, FrequentlyAskedQuestion, TermsOfUse
from base_utils.base_tests import TainoBaseAdminAPITestCase


class FrequentlyAskedQuestionAdminAPITest(TainoBaseAdminAPITestCase):
    def setUp(self):
        super().setUp()
        self.faq = baker.make(FrequentlyAskedQuestion, question="Test Question", answer="Test Answer", is_active=True)
        self.url = reverse("common:about_us_admin:frequently-questions-list")
        self.detail_url = reverse("common:about_us_admin:frequently-questions-detail", args=[self.faq.pid])

    def test_list_faqs(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_faq(self):
        data = {"question": "New FAQ Question", "answer": "New FAQ Answer", "order": 1, "is_active": True}

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["question"], data["question"])
        self.assertEqual(response.data["answer"], data["answer"])

    def test_update_faq(self):
        data = {"question": "Updated FAQ Question", "answer": "Updated FAQ Answer"}

        response = self.client.patch(self.detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["question"], data["question"])
        self.assertEqual(response.data["answer"], data["answer"])
