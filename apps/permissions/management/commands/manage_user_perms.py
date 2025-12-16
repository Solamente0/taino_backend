from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from apps.permissions.models import Permission, UserPermission, PermissionCategory
from apps.permissions.services.permissions import PermissionService

User = get_user_model()


class Command(BaseCommand):
    help = 'Manages user permissions - add or remove permissions by category or code'

    def add_arguments(self, parser):
        # Required arguments
        parser.add_argument('user_identifier', type=str, help='User identifier (vekalat_id, email, or phone_number)')

        # Optional arguments
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            '--all',
            action='store_true',
            help='Add all permissions',
        )
        group.add_argument(
            '--category',
            type=str,
            help='Permission category name to add all permissions from',
        )
        group.add_argument(
            '--permission',
            type=str,
            help='Specific permission code_name to add',
        )

        parser.add_argument(
            '--remove',
            action='store_true',
            help='Remove specified permissions instead of adding them',
        )

        parser.add_argument(
            '--list',
            action='store_true',
            help='List current permissions for the user',
        )

    def handle(self, *args, **options):
        user_identifier = options['user_identifier']
        remove_mode = options.get('remove', False)
        list_mode = options.get('list', False)

        # Find the user by vekalat_id, email, or phone_number
        try:
            user = User.objects.get(vekalat_id=user_identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=user_identifier)
            except User.DoesNotExist:
                try:
                    user = User.objects.get(phone_number=user_identifier)
                except User.DoesNotExist:
                    raise CommandError(f'User with identifier "{user_identifier}" does not exist')

        # List user's current permissions
        if list_mode:
            self._list_user_permissions(user)
            return

        # Process based on command options
        if options.get('all'):
            self._handle_all_permissions(user, remove_mode)
        elif options.get('category'):
            self._handle_category_permissions(user, options['category'], remove_mode)
        elif options.get('permission'):
            self._handle_specific_permission(user, options['permission'], remove_mode)
        else:
            # If no option is provided, show help
            self.stdout.write('Please specify one of --all, --category, --permission, or --list')
            self.stdout.write('Use --help for more information')

    def _list_user_permissions(self, user):
        # Get all permissions for the user including role permissions
        permissions = PermissionService.get_user_permissions(user)

        if not permissions:
            self.stdout.write(self.style.WARNING(f'User "{user.get_full_name()}" has no permissions'))
            return

        self.stdout.write(self.style.SUCCESS(f'Permissions for user "{user.get_full_name()}":'))

        # Group by category for better readability
        permissions_by_category = {}
        for perm in permissions:
            category_name = perm.category.name
            if category_name not in permissions_by_category:
                permissions_by_category[category_name] = []
            permissions_by_category[category_name].append(perm)

        for category, perms in permissions_by_category.items():
            self.stdout.write(f'\n{category}:')
            for perm in perms:
                self.stdout.write(f'  - {perm.name} ({perm.code_name})')

    def _handle_all_permissions(self, user, remove_mode):
        permissions = Permission.objects.filter(is_active=True)

        if remove_mode:
            # Remove all permissions
            deleted_count, _ = UserPermission.objects.filter(user=user).delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully removed {deleted_count} permissions from user "{user.get_full_name()}"')
            )
        else:
            # Add all permissions
            added_count = 0
            for permission in permissions:
                user_permission, created = UserPermission.objects.get_or_create(
                    user=user,
                    permission=permission,
                    defaults={'is_granted': True}
                )

                if not created and not user_permission.is_granted:
                    user_permission.is_granted = True
                    user_permission.save()
                    added_count += 1
                elif created:
                    added_count += 1

            self.stdout.write(
                self.style.SUCCESS(f'Successfully added {added_count} permissions to user "{user.get_full_name()}"')
            )

    def _handle_category_permissions(self, user, category_name, remove_mode):
        try:
            category = PermissionCategory.objects.get(name=category_name)
        except PermissionCategory.DoesNotExist:
            raise CommandError(f'Permission category "{category_name}" does not exist')

        permissions = Permission.objects.filter(category=category, is_active=True)

        if remove_mode:
            # Remove permissions in the category
            deleted_count, _ = UserPermission.objects.filter(user=user, permission__category=category).delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully removed {deleted_count} permissions in category "{category_name}" '
                    f'from user "{user.get_full_name()}"'
                )
            )
        else:
            # Add permissions in the category
            added_count = 0
            for permission in permissions:
                user_permission, created = UserPermission.objects.get_or_create(
                    user=user,
                    permission=permission,
                    defaults={'is_granted': True}
                )

                if not created and not user_permission.is_granted:
                    user_permission.is_granted = True
                    user_permission.save()
                    added_count += 1
                elif created:
                    added_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully added {added_count} permissions in category "{category_name}" '
                    f'to user "{user.get_full_name()}"'
                )
            )

    def _handle_specific_permission(self, user, permission_code, remove_mode):
        try:
            permission = Permission.objects.get(code_name=permission_code, is_active=True)
        except Permission.DoesNotExist:
            raise CommandError(f'Permission with code_name "{permission_code}" does not exist or is not active')

        if remove_mode:
            # Remove the specific permission
            deleted, _ = UserPermission.objects.filter(user=user, permission=permission).delete()
            if deleted:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully removed permission "{permission.name}" ({permission_code}) '
                        f'from user "{user.get_full_name()}"'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'User "{user.get_full_name()}" did not have permission "{permission.name}" ({permission_code})'
                    )
                )
        else:
            # Add the specific permission
            user_permission, created = UserPermission.objects.get_or_create(
                user=user,
                permission=permission,
                defaults={'is_granted': True}
            )

            if not created and not user_permission.is_granted:
                user_permission.is_granted = True
                user_permission.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully updated permission "{permission.name}" ({permission_code}) '
                        f'for user "{user.get_full_name()}"'
                    )
                )
            elif created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully added permission "{permission.name}" ({permission_code}) '
                        f'to user "{user.get_full_name()}"'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'User "{user.get_full_name()}" already has permission "{permission.name}" ({permission_code})'
                    )
                )