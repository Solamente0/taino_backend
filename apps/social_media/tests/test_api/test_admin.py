from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from apps.document.models import TainoDocument
from apps.social_media.models import SocialMediaType
from base_utils.base_tests import TainoBaseAPITestCase


class SocialMediaTypeAdminCreateUpdateAPITest(TainoBaseAPITestCase):

    def setUp(self):
        super().setUp()
        self.document = baker.make(TainoDocument)
        self.user.is_admin = True
        self.user.save()
        self.url = reverse("social_media:social_media_admin:social_media_admin-list")

    def test_social_media_creation(self):
        data = {
            "type": "telegram",
            "link": self.faker.url(),
            "file": self.document.pid,
            "is_active": True,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SocialMediaType.objects.count(), 1)


class SocialMediaTypeAdminListAPITest(TainoBaseAPITestCase):

    def setUp(self):
        super().setUp()
        self.social_media_counts = 3
        self.social_medias = baker.make(SocialMediaType, _quantity=self.social_media_counts)
        self.url = reverse("social_media:social_media_admin:social_media_admin-list")
        self.user.is_admin = True
        self.user.save()

    def test_social_media_list(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), self.social_media_counts)

    def test_social_media_list_see_inactive_objects(self):
        baker.make(SocialMediaType, _quantity=self.social_media_counts, is_active=False)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), self.social_media_counts * 2)

    def test_social_media_list_without_being_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
