import json
import os
from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _

from apps.authentication.models import UserType
from apps.permissions.models import Permission, PermissionCategory, UserTypePermission


class Command(BaseCommand):
    help = _("Set up initial permissions and assign them to user types")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting permission setup..."))

        # Create permission categories and permissions from JSON file
        try:
            permissions_data = self._load_permissions_data()
            created_permissions = self._create_permissions(permissions_data)

            # Assign default permissions to user types
            self._assign_default_permissions(permissions_data.get("default_assignments", {}))

            self.stdout.write(self.style.SUCCESS(f"Successfully created {len(created_permissions)} permissions"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))

    def _load_permissions_data(self):
        """
        Load permissions data from JSON file
        """
        # Path is relative to the project root
        file_path = os.path.join("apps", "permission", "fixtures", "permissions.json")

        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING(f"Permissions file not found at {file_path}. Creating empty structure."))
            return {"categories": [], "default_assignments": {}}

    def _create_permissions(self, permissions_data):
        """
        Create permission categories and permissions
        """
        created_permissions = []

        for category_data in permissions_data.get("categories", []):
            category_name = category_data.get("name")
            category_description = category_data.get("description", "")

            category, created = PermissionCategory.objects.get_or_create(
                name=category_name, defaults={"description": category_description}
            )

            if created:
                self.stdout.write(f"Created category: {category_name}")

            # Create permissions for this category
            for permission_data in category_data.get("permissions", []):
                permission_name = permission_data.get("name")
                permission_code = permission_data.get("code_name")
                permission_description = permission_data.get("description", "")

                permission, created = Permission.objects.get_or_create(
                    code_name=permission_code,
                    defaults={
                        "name": permission_name,
                        "description": permission_description,
                        "category": category,
                        "is_active": True,
                    },
                )

                if created:
                    created_permissions.append(permission)
                    self.stdout.write(f"  Created permission: {permission_name} ({permission_code})")
                else:
                    # Update existing permission if needed
                    if permission.name != permission_name or permission.description != permission_description:
                        permission.name = permission_name
                        permission.description = permission_description
                        permission.save()
                        self.stdout.write(f"  Updated permission: {permission_name} ({permission_code})")

        return created_permissions

    def _assign_default_permissions(self, default_assignments):
        """
        Assign default permissions to user types
        """
        for user_type_name, permission_codes in default_assignments.items():
            try:
                # Get or create user type
                user_type, created = UserType.objects.get_or_create(name=user_type_name)

                if created:
                    self.stdout.write(f"Created user type: {user_type_name}")

                # Get permissions by code names
                permissions = Permission.objects.filter(code_name__in=permission_codes)

                # Assign permissions to user type
                for permission in permissions:
                    UserTypePermission.objects.get_or_create(user_type=user_type, permission=permission)

                self.stdout.write(
                    self.style.SUCCESS(f"Assigned {permissions.count()} permissions to user type: {user_type_name}")
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error assigning permissions to user type {user_type_name}: {str(e)}"))
