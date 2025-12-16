import logging

from django.contrib.auth import get_user_model
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from base_utils.base_tests import TainoBaseAPITestCase

log = logging.getLogger(__name__)
User = get_user_model()


class UserDeleteAccountAPITestCase(TainoBaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.old_phone_number = self.user.phone_number
        self.old_email = self.user.email

        self.user_with_email = baker.make(User, email="dummy@gmail.com", phone_number=None)
        self.user_with_phone_number = baker.make(User, email=None, phone_number="989307605866")

        self.url = reverse("user:user_v1:user_delete_account")

    def test_user_delete_account_success(self):
        response = self.client.post(self.url)
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(self.user.is_active)
        self.assertEqual(self.user.phone_number, "#_" + self.old_phone_number)
        self.assertEqual(self.user.email, "#_" + self.old_email)

        # test create user with old number and email successfully!
        new_user = baker.make(User, email=self.old_email, phone_number=self.old_phone_number, is_active=True)
        self.assertIsNotNone(new_user)

    def test_user_has_only_email_delete_account_success(self):
        old_email = self.user_with_email.email
        old_phone_number = self.user_with_email.phone_number

        self.client.force_authenticate(self.user_with_email)

        response = self.client.post(self.url)

        self.user_with_email.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(self.user_with_email.is_active)
        self.assertIsNone(old_phone_number)
        self.assertEqual(self.user_with_email.email, "#_" + old_email)

        # test create user with old email successfully!
        new_user = baker.make(User, email=old_email, phone_number=old_phone_number, is_active=True)
        self.assertIsNotNone(new_user)

    def test_user_has_only_phone_number_delete_account_success(self):
        old_email = self.user_with_phone_number.email
        old_phone_number = self.user_with_phone_number.phone_number

        self.client.force_authenticate(self.user_with_phone_number)

        response = self.client.post(self.url)

        self.user_with_phone_number.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(self.user_with_phone_number.is_active)
        self.assertIsNone(old_email)
        self.assertEqual(self.user_with_phone_number.phone_number, "#_" + old_phone_number)

        # test create user with old number successfully!
        new_user = baker.make(User, email=old_email, phone_number=old_phone_number, is_active=True)
        self.assertIsNotNone(new_user)
