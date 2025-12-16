from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from apps.permissions.models import Permission, PermissionCategory, UserPermission, UserTypePermission
from base_utils.base_tests import TainoBaseAPITestCase


class PermissionCategoryV1APITest(TainoBaseAPITestCase):
    """
    Tests for the permission category V1 API
    """

    def setUp(self):
        super().setUp()
        self.url = reverse("permission:permission_v1:permission_categories-list")
        self.category = baker.make(PermissionCategory, name="Test Category")

    def test_list_permission_categories(self):
        # Get list of permission categories
        response = self.client.get(self.url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Test Category")

    def test_list_permission_categories_unauthorized(self):
        # Logout
        self.client.logout()

        # Try to get list of permission categories
        response = self.client.get(self.url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PermissionV1APITest(TainoBaseAPITestCase):
    """
    Tests for the permission V1 API
    """

    def setUp(self):
        super().setUp()
        self.category = baker.make(PermissionCategory, name="Test Category")
        self.permission1 = baker.make(
            Permission, name="Test Permission 1", code_name="test.permission1", category=self.category, is_active=True
        )
        self.permission2 = baker.make(
            Permission, name="Test Permission 2", code_name="test.permission2", category=self.category, is_active=True
        )
        self.inactive_permission = baker.make(
            Permission, name="Inactive Permission", code_name="test.inactive", category=self.category, is_active=False
        )

        # Create a user type (group)
        from apps.authentication.models import UserType

        self.user_type = baker.make(Group, name="Test Group")

        # Add user to group
        self.user.groups.add(self.user_type)

        # Assign permissions
        baker.make(UserTypePermission, user_type=self.user_type, permission=self.permission1)
        baker.make(UserPermission, user=self.user, permission=self.permission2, is_granted=True)

        self.url = reverse("permission:permission_v1:permissions-list")
        self.check_url = reverse("permission:permission_v1:permissions-check")
        self.my_permissions_url = reverse("permission:permission_v1:permissions-my_permissions")

    def test_list_permissions(self):
        # Get list of permissions
        response = self.client.get(self.url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only active permissions

        permission_codes = [p["code_name"] for p in response.data]
        self.assertIn("test.permission1", permission_codes)
        self.assertIn("test.permission2", permission_codes)
        self.assertNotIn("test.inactive", permission_codes)

    def test_check_permission_has_permission(self):
        # Check permission that user has
        data = {"permission_code": "test.permission1"}
        response = self.client.post(self.check_url, data)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["permission_code"], "test.permission1")
        self.assertTrue(response.data["has_permission"])

    def test_check_permission_does_not_have_permission(self):
        # Check permission that user doesn't have
        data = {"permission_code": "test.nonexistent"}
        response = self.client.post(self.check_url, data)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["permission_code"], "test.nonexistent")
        self.assertFalse(response.data["has_permission"])

    def test_my_permissions(self):
        # Get user's permissions
        response = self.client.get(self.my_permissions_url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        permission_codes = [p["code_name"] for p in response.data]
        self.assertIn("test.permission1", permission_codes)
        self.assertIn("test.permission2", permission_codes)

    def test_api_unauthorized(self):
        # Logout
        self.client.logout()

        # Try to get list of permissions
        response = self.client.get(self.url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Try to check permission
        response = self.client.post(self.check_url, {"permission_code": "test.permission1"})

        # Check response
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Try to get user's permissions
        response = self.client.get(self.my_permissions_url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
