from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from apps.social_media.models import SocialMediaType
from base_utils.base_tests import TainoBaseAPITestCase


class SocialMediaTypeListAPITest(TainoBaseAPITestCase):

    def setUp(self):
        super().setUp()
        self.social_media_counts = 3
        self.social_medias = baker.make(SocialMediaType, _quantity=self.social_media_counts)
        self.url = reverse("social_media:social_media_v1:social_media-list")

    def test_social_media_list(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), self.social_media_counts)

    def test_social_media_list_without_being_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
