from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from apps.banner.models import Banner
from apps.document.models import TainoDocument
from base_utils.base_tests import TainoBaseAPITestCase


class BannerAdminCreateUpdateAPITest(TainoBaseAPITestCase):

    def setUp(self):
        super().setUp()
        self.document = baker.make(TainoDocument)
        self.user.is_admin = True
        self.user.save()

        self.url = reverse("banner:banner_admin:banner-list")

    def test_banner_creation_with_department(self):
        data = {"link": "http://example.com", "file": self.document.pid, "is_active": True}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Banner.objects.count(), 1)

    def test_banner_creation_with_profile_category(self):
        data = {"link": "http://example.com", "file": self.document.pid, "is_active": True}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Banner.objects.count(), 1)

    def test_banner_creation_with_both_department_and_profile_category_not_allowed(self):
        data = {
            "link": "http://example.com",
            "file": self.document.pid,
            "is_active": True,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Banner.objects.count(), 0)


class BannerAdminListAPITest(TainoBaseAPITestCase):

    def setUp(self):
        super().setUp()
        self.banner_counts = 3
        self.banners = baker.make(Banner, _quantity=self.banner_counts)
        self.url = reverse("banner:banner_admin:banner-list")

        self.user.is_admin = True
        self.user.save()

    def test_banner_list(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), self.banner_counts)

    def test_banner_list_see_inactive_objects(self):
        baker.make(Banner, _quantity=self.banner_counts, is_active=False)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), self.banner_counts * 2)

    def test_banner_list_without_being_login(self):
        self.client.logout()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
