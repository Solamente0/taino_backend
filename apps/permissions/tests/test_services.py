from apps.permissions.services.permissions import PermissionService

from django.contrib.auth import get_user_model
from model_bakery import baker

from apps.permissions.models import Permission, PermissionCategory, UserPermission, UserTypePermission
from apps.permissions.services.query import PermissionQuery
from base_utils.base_tests import TainoBaseServiceTestCase


User = get_user_model()


class PermissionServiceTest(TainoBaseServiceTestCase):
    """
    Tests for the PermissionService
    """

    def setUp(self):
        super().setUp()
        # Create test data
        self.category = baker.make(PermissionCategory, name="Test Category")
        self.permission1 = baker.make(
            Permission, name="Test Permission 1", code_name="test.permission1", category=self.category, is_active=True
        )
        self.permission2 = baker.make(
            Permission, name="Test Permission 2", code_name="test.permission2", category=self.category, is_active=True
        )
        self.permission3 = baker.make(
            Permission, name="Test Permission 3", code_name="test.permission3", category=self.category, is_active=False
        )

        # Create a user type (group)
        from apps.authentication.models import UserType

        self.user_type = baker.make(Group, name="Test Group")

        # Add user to group
        self.user.groups.add(self.user_type)

        # Create another user
        self.user2 = baker.make(User)

    def test_has_permission_for_user_type(self):
        # Assign permission to user type
        baker.make(UserTypePermission, user_type=self.user_type, permission=self.permission1)

        # Check if user has permission
        has_permission = PermissionService.has_permission(self.user, "test.permission1")
        self.assertTrue(has_permission)

        # Check if user doesn't have permission
        has_permission = PermissionService.has_permission(self.user, "test.permission2")
        self.assertFalse(has_permission)

        # Check inactive permission
        has_permission = PermissionService.has_permission(self.user, "test.permission3")
        self.assertFalse(has_permission)

        # Check for user not in group
        has_permission = PermissionService.has_permission(self.user2, "test.permission1")
        self.assertFalse(has_permission)

    def test_has_permission_for_user_direct(self):
        # Assign permission to user directly
        baker.make(UserPermission, user=self.user, permission=self.permission2, is_granted=True)

        # Check if user has permission
        has_permission = PermissionService.has_permission(self.user, "test.permission2")
        self.assertTrue(has_permission)

    def test_has_permission_denied_explicit(self):
        # Assign permission to user type
        baker.make(UserTypePermission, user_type=self.user_type, permission=self.permission1)

        # Deny permission to user explicitly
        baker.make(UserPermission, user=self.user, permission=self.permission1, is_granted=False)

        # Check if user doesn't have permission
        has_permission = PermissionService.has_permission(self.user, "test.permission1")
        self.assertFalse(has_permission)

    def test_get_user_permissions(self):
        # Assign permissions
        baker.make(UserTypePermission, user_type=self.user_type, permission=self.permission1)
        baker.make(UserPermission, user=self.user, permission=self.permission2, is_granted=True)
        baker.make(UserTypePermission, user_type=self.user_type, permission=self.permission3)  # inactive

        # Get user permissions
        permissions = PermissionService.get_user_permissions(self.user)

        # Should have 2 permissions (permission1 from user type, permission2 from direct)
        self.assertEqual(permissions.count(), 2)
        self.assertIn(self.permission1, permissions)
        self.assertIn(self.permission2, permissions)
        self.assertNotIn(self.permission3, permissions)  # Inactive permission

    def test_assign_permission_to_user(self):
        # Assign permission to user
        user_permission = PermissionService.assign_permission_to_user(self.user, "test.permission1", True)

        # Check if permission is assigned
        self.assertEqual(user_permission.user, self.user)
        self.assertEqual(user_permission.permission, self.permission1)
        self.assertTrue(user_permission.is_granted)

        # Check if user has permission
        has_permission = PermissionService.has_permission(self.user, "test.permission1")
        self.assertTrue(has_permission)

    def test_assign_permission_to_user_type(self):
        # Assign permission to user type
        user_type_permission = PermissionService.assign_permission_to_user_type(self.user_type.pid, "test.permission1")

        # Check if permission is assigned
        self.assertEqual(user_type_permission.user_type, self.user_type)
        self.assertEqual(user_type_permission.permission, self.permission1)

        # Check if user has permission
        has_permission = PermissionService.has_permission(self.user, "test.permission1")
        self.assertTrue(has_permission)

    def test_remove_permission_from_user(self):
        # Assign permission to user
        PermissionService.assign_permission_to_user(self.user, "test.permission1", True)

        # Remove permission from user
        result = PermissionService.remove_permission_from_user(self.user, "test.permission1")

        # Check if permission is removed
        self.assertTrue(result)
        self.assertFalse(UserPermission.objects.filter(user=self.user, permission=self.permission1).exists())

    def test_remove_permission_from_user_type(self):
        # Assign permission to user type
        PermissionService.assign_permission_to_user_type(self.user_type.pid, "test.permission1")

        # Remove permission from user type
        result = PermissionService.remove_permission_from_user_type(self.user_type.pid, "test.permission1")

        # Check if permission is removed
        self.assertTrue(result)
        self.assertFalse(UserTypePermission.objects.filter(user_type=self.user_type, permission=self.permission1).exists())


class PermissionQueryTest(TainoBaseServiceTestCase):
    """
    Tests for the PermissionQuery service
    """

    def setUp(self):
        super().setUp()
        # Create test data
        self.category1 = baker.make(PermissionCategory, name="Test Category 1")
        self.category2 = baker.make(PermissionCategory, name="Test Category 2")

        self.permission1 = baker.make(
            Permission, name="Test Permission 1", code_name="test.permission1", category=self.category1, is_active=True
        )
        self.permission2 = baker.make(
            Permission, name="Test Permission 2", code_name="test.permission2", category=self.category1, is_active=True
        )
        self.permission3 = baker.make(
            Permission, name="Test Permission 3", code_name="test.permission3", category=self.category2, is_active=True
        )
        self.permission4 = baker.make(
            Permission, name="Test Permission 4", code_name="test.permission4", category=self.category2, is_active=False
        )

        # Create a user type (group)
        from apps.authentication.models import UserType

        self.user_type = baker.make(Group, name="Test Group")

        # Add user to group
        self.user.groups.add(self.user_type)

        # Assign permissions
        baker.make(UserTypePermission, user_type=self.user_type, permission=self.permission1)
        baker.make(UserPermission, user=self.user, permission=self.permission3, is_granted=True)

    def test_get_active_permissions(self):
        # Get active permissions
        permissions = PermissionQuery.get_active_permissions()

        # Should have 3 active permissions
        self.assertEqual(permissions.count(), 3)
        self.assertIn(self.permission1, permissions)
        self.assertIn(self.permission2, permissions)
        self.assertIn(self.permission3, permissions)
        self.assertNotIn(self.permission4, permissions)  # Inactive permission

    def test_get_active_permission_categories(self):
        # Get active permission categories
        categories = PermissionQuery.get_active_permission_categories()

        # Should have 2 categories with active permissions
        self.assertEqual(categories.count(), 2)
        self.assertIn(self.category1, categories)
        self.assertIn(self.category2, categories)

    def test_get_user_permissions(self):
        # Get user permissions
        user_permissions = PermissionQuery.get_user_permissions(self.user.pid)

        # Should have 1 direct user permission
        self.assertEqual(user_permissions.count(), 1)
        user_permission = user_permissions.first()
        self.assertEqual(user_permission.user, self.user)
        self.assertEqual(user_permission.permission, self.permission3)

    def test_get_user_type_permissions(self):
        # Get user type permissions
        user_type_permissions = PermissionQuery.get_user_type_permissions(self.user_type.pid)

        # Should have 1 user type permission
        self.assertEqual(user_type_permissions.count(), 1)
        user_type_permission = user_type_permissions.first()
        self.assertEqual(user_type_permission.user_type, self.user_type)
        self.assertEqual(user_type_permission.permission, self.permission1)

    def test_get_permissions_by_category(self):
        # Get permissions by category
        permissions_by_category = PermissionQuery.get_permissions_by_category()

        # Should have 2 categories
        self.assertEqual(len(permissions_by_category), 2)

        # Category 1 should have 2 permissions
        self.assertIn(self.category1.name, permissions_by_category)
        category1_permissions = permissions_by_category[self.category1.name]
        self.assertEqual(len(category1_permissions), 2)
        self.assertIn(self.permission1, category1_permissions)
        self.assertIn(self.permission2, category1_permissions)

        # Category 2 should have 1 active permission
        self.assertIn(self.category2.name, permissions_by_category)
        category2_permissions = permissions_by_category[self.category2.name]
        self.assertEqual(len(category2_permissions), 1)
        self.assertIn(self.permission3, category2_permissions)
        self.assertNotIn(self.permission4, category2_permissions)  # Inactive permission
