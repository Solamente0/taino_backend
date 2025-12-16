from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from apps.authentication.models import TainoUser
from base_utils.base_tests import TainoBaseAPITestCase


class GoogleLoginTestCase(TainoBaseAPITestCase):
    def setUp(self):
        # self.google_redirect_url = reverse("api:authentication:google-oauth2:login-sdk:redirect-sdk")
        # self.google_callback_url = reverse("api:authentication:google-oauth2:login-sdk:callback-sdk")
        self.url = reverse("authentication:authentication_v1:google_login")
        self.client.logout()
        self.email = "googleauth@gmail.com"
        self.first_name = "googleauth_first_name"
        self.last_name = "googleauth_last_name"
        self.code = "123qwe!@#"
        self.error = ""

    @patch("apps.authentication.services.google_auth.HttpRequestManager.get")
    @patch("apps.authentication.services.google_auth.HttpRequestManager.post")
    def test_google_login_create_user_successfully(self, mock_access_token, mock_user_data):
        mock_access_token.return_value.json.return_value = {"access_token": "asdzxc"}
        mock_user_data.return_value.json.return_value = {
            "email": self.email,
            "given_name": self.first_name,
            "family_name": self.last_name,
        }
        response = self.client.post(self.url, data={"code": self.code, "error": self.error})
        query = TainoUser.objects.filter(email=self.email)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(query.exists())

    @patch("apps.authentication.services.google_auth.HttpRequestManager.get")
    @patch("apps.authentication.services.google_auth.HttpRequestManager.post")
    def test_google_login_existed_user_successfully(self, mock_access_token, mock_user_data):
        baker.make(get_user_model(), email=self.email)
        mock_access_token.return_value.json.return_value = {"access_token": "asdzxc"}
        mock_user_data.return_value.json.return_value = {
            "email": self.email,
            "given_name": self.first_name,
            "family_name": self.last_name,
        }
        response = self.client.post(self.url, data={"code": self.code, "error": self.error})
        query = TainoUser.objects.filter(email=self.email)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(query.count(), 1)
        self.assertTrue(query.exists())

    @patch("apps.authentication.services.google_auth.HttpRequestManager.get")
    @patch("apps.authentication.services.google_auth.HttpRequestManager.post")
    def test_google_login_with_error(self, mock_access_token, mock_user_data):
        mock_access_token.return_value.json.return_value = {"access_token": "asdzxc"}
        mock_user_data.return_value.json.return_value = {
            "email": self.email,
            "given_name": self.first_name,
            "family_name": self.last_name,
        }
        response = self.client.post(self.url, data={"code": self.code, "error": "an error"})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        query = TainoUser.objects.filter(email=self.email)
        self.assertEqual(query.count(), 0)
