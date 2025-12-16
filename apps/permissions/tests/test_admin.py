from django.contrib.auth import get_user_model
from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from apps.permissions.models import Permission, PermissionCategory, UserPermission, UserTypePermission
from base_utils.base_tests import TainoBaseAPITestCase


class PermissionCategoryAdminAPITest(TainoBaseAPITestCase):
    """
    Tests for the permission category admin API
    """

    def setUp(self):
        super().setUp()
        self.user.is_admin = True
        self.user.save()

        self.url = reverse("permission:permission_admin:permission_categories-list")
        self.category = baker.make(PermissionCategory, name="Test Category")

    def test_list_permission_categories(self):
        # Get list of permission categories
        response = self.client.get(self.url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Test Category")

    def test_create_permission_category(self):
        # Create permission category
        data = {"name": "New Category", "description": "New category description"}
        response = self.client.post(self.url, data)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Category")
        self.assertEqual(response.data["description"], "New category description")

        # Check database
        self.assertTrue(PermissionCategory.objects.filter(name="New Category").exists())


class PermissionAdminAPITest(TainoBaseAPITestCase):
    """
    Tests for the permission admin API
    """

    def setUp(self):
        super().setUp()
        self.user.is_admin = True
        self.user.save()

        self.category = baker.make(PermissionCategory, name="Test Category")
        self.permission = baker.make(
            Permission, name="Test Permission", code_name="test.permission", category=self.category, is_active=True
        )

        self.url = reverse("permission:permission_admin:permissions-list")

    def test_list_permissions(self):
        # Get list of permissions
        response = self.client.get(self.url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Test Permission")
        self.assertEqual(response.data[0]["code_name"], "test.permission")
        self.assertEqual(response.data[0]["category"]["name"], "Test Category")

    def test_create_permission(self):
        # Create permission
        data = {
            "name": "New Permission",
            "description": "New permission description",
            "code_name": "test.new_permission",
            "category_id": self.category.pid,
            "is_active": True,
        }
        response = self.client.post(self.url, data)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Permission")
        self.assertEqual(response.data["code_name"], "test.new_permission")
        self.assertEqual(response.data["category"]["name"], "Test Category")

        # Check database
        self.assertTrue(Permission.objects.filter(code_name="test.new_permission").exists())


class UserTypePermissionAdminAPITest(TainoBaseAPITestCase):
    """
    Tests for the user type permission admin API
    """

    def setUp(self):
        super().setUp()
        self.user.is_admin = True
        self.user.save()

        self.category = baker.make(PermissionCategory, name="Test Category")
        self.permission1 = baker.make(
            Permission, name="Test Permission 1", code_name="test.permission1", category=self.category, is_active=True
        )
        self.permission2 = baker.make(
            Permission, name="Test Permission 2", code_name="test.permission2", category=self.category, is_active=True
        )

        from apps.authentication.models import UserType

        self.user_type = baker.make(UserType, name="Test Group")
        self.user_type_permission = baker.make(UserTypePermission, user_type=self.user_type, permission=self.permission1)

        self.url = reverse("permission:permission_admin:user_type_permissions-list")
        self.bulk_assign_url = reverse("permission:permission_admin:user_type_permissions-bulk_assign")
        self.bulk_remove_url = reverse("permission:permission_admin:user_type_permissions-bulk_remove")

    def test_list_user_type_permissions(self):
        # Get list of user type permissions
        response = self.client.get(self.url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["user_type_name"], "Test Group")
        self.assertEqual(response.data[0]["permission"]["name"], "Test Permission 1")

    def test_create_user_type_permission(self):
        # Create user type permission
        data = {"user_type": self.user_type.pid, "permission_id": self.permission2.pid}
        response = self.client.post(self.url, data)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user_type_name"], "Test Group")
        self.assertEqual(response.data["permission"]["name"], "Test Permission 2")

        # Check database
        self.assertTrue(UserTypePermission.objects.filter(user_type=self.user_type, permission=self.permission2).exists())

    def test_bulk_assign_permissions_to_user_type(self):
        # Bulk assign permissions
        data = {"user_type_id": self.user_type.pid, "permission_ids": [self.permission2.pid]}
        response = self.client.post(self.bulk_assign_url, data, format="json")

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["permission"]["name"], "Test Permission 2")

        # Check database
        self.assertTrue(UserTypePermission.objects.filter(user_type=self.user_type, permission=self.permission2).exists())

    def test_bulk_remove_permissions_from_user_type(self):
        # Bulk remove permissions
        url = f"{self.bulk_remove_url}?user_type_id={self.user_type.pid}&permission_ids={self.permission1.pid}"
        response = self.client.delete(url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Check database
        self.assertFalse(UserTypePermission.objects.filter(user_type=self.user_type, permission=self.permission1).exists())


class UserPermissionAdminAPITest(TainoBaseAPITestCase):
    """
    Tests for the user permission admin API
    """

    def setUp(self):
        super().setUp()
        self.user.is_admin = True
        self.user.save()

        self.category = baker.make(PermissionCategory, name="Test Category")
        self.permission1 = baker.make(
            Permission, name="Test Permission 1", code_name="test.permission1", category=self.category, is_active=True
        )
        self.permission2 = baker.make(
            Permission, name="Test Permission 2", code_name="test.permission2", category=self.category, is_active=True
        )

        self.test_user = baker.make(get_user_model(), first_name="Test", last_name="User")
        self.user_permission = baker.make(UserPermission, user=self.test_user, permission=self.permission1, is_granted=True)

        self.url = reverse("permission:permission_admin:user_permissions-list")
        self.bulk_assign_url = reverse("permission:permission_admin:user_permissions-bulk_assign")
        self.bulk_remove_url = reverse("permission:permission_admin:user_permissions-bulk_remove")

    def test_list_user_permissions(self):
        # Get list of user permissions
        response = self.client.get(self.url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["username"], "Test User")
        self.assertEqual(response.data[0]["permission"]["name"], "Test Permission 1")
        self.assertTrue(response.data[0]["is_granted"])

    def test_create_user_permission(self):
        # Create user permission
        data = {"user": self.test_user.pid, "permission_id": self.permission2.pid, "is_granted": True}
        response = self.client.post(self.url, data)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "Test User")
        self.assertEqual(response.data["permission"]["name"], "Test Permission 2")
        self.assertTrue(response.data["is_granted"])

        # Check database
        self.assertTrue(
            UserPermission.objects.filter(user=self.test_user, permission=self.permission2, is_granted=True).exists()
        )

    def test_bulk_assign_permissions_to_user(self):
        # Bulk assign permissions
        data = {"user_id": self.test_user.pid, "permission_ids": [self.permission2.pid], "is_granted": False}
        response = self.client.post(self.bulk_assign_url, data, format="json")

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["permission"]["name"], "Test Permission 2")
        self.assertFalse(response.data[0]["is_granted"])

        # Check database
        self.assertTrue(
            UserPermission.objects.filter(user=self.test_user, permission=self.permission2, is_granted=False).exists()
        )

    def test_bulk_remove_permissions_from_user(self):
        # Bulk remove permissions
        url = f"{self.bulk_remove_url}?user_id={self.test_user.pid}&permission_ids={self.permission1.pid}"
        response = self.client.delete(url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Check database
        self.assertFalse(UserPermission.objects.filter(user=self.test_user, permission=self.permission1).exists())
