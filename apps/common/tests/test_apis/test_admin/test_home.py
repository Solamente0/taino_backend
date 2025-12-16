from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from apps.common.models import HomePage, FrequentlyAskedQuestion, TermsOfUse
from base_utils.base_tests import TainoBaseAdminAPITestCase


class HomePageAdminAPITest(TainoBaseAdminAPITestCase):
    def setUp(self):
        super().setUp()
        self.homepage = baker.make(
            HomePage, header_title="Test Header Title", header_sub_title="Test Header Subtitle", is_active=True
        )
        self.url = reverse("common:about_us_admin:homepages-list")
        self.detail_url = reverse("common:about_us_admin:homepages-detail", args=[self.homepage.pid])

    def test_list_homepages(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_retrieve_homepage(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["header_title"], self.homepage.header_title)
        self.assertEqual(response.data["header_sub_title"], self.homepage.header_sub_title)

    def test_create_homepage(self):
        data = {
            "header_title": "New Header Title",
            "header_sub_title": "New Header Subtitle",
            "why": "New Why Section",
            "why_point1": "New Point 1",
            "why_point2": "New Point 2",
            "why_point3": "New Point 3",
            "why_point4": "New Point 4",
            "is_active": True,
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["header_title"], data["header_title"])
        self.assertEqual(response.data["why_point1"], data["why_point1"])

    def test_update_homepage(self):
        data = {"header_title": "Updated Header Title", "why_point1": "Updated Point 1"}

        response = self.client.patch(self.detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["header_title"], data["header_title"])
        self.assertEqual(response.data["why_point1"], data["why_point1"])
        # Ensure other fields aren't changed
        self.assertEqual(response.data["header_sub_title"], self.homepage.header_sub_title)

    def test_delete_homepage(self):
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(HomePage.objects.filter(pid=self.homepage.pid).count(), 0)
