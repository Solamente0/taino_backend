from unittest import skip

from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from apps.banner.models import Banner, BannerTranslation
from base_utils.base_tests import TainoBaseAPITestCase


class BannerListAPITest(TainoBaseAPITestCase):

    def setUp(self):
        super().setUp()
        self.banner_counts = 3
        self.banners = baker.make(Banner, _quantity=self.banner_counts)
        self.url = reverse("banner:banner_v1:banner-list")

    def test_banner_list(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), self.banner_counts)

    @skip("TODO Change Permissions")
    def test_banner_list_without_being_login(self):
        self.client.logout()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BannerTranslationAPITest(TainoBaseAPITestCase):

    def setUp(self):
        super().setUp()
        self.banner = baker.make(Banner, link="http://test.com")
        self.banner_translation = baker.make(
            BannerTranslation, link="http://test-persian.com", main_object=self.banner, language_code="fa"
        )

        self.url = reverse("banner:banner_v1:banner-list")

    def test_banner_list_with_language_code(self):
        response = self.client.get(self.url, headers={"Accept-Language": "fa"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        instance_data = response.data[0]
        self.assertEqual(instance_data["link"], self.banner_translation.link)
        self.banner.refresh_from_db()
        self.assertNotEquals(self.banner.link, self.banner_translation.link)
