from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from apps.permissions.models import Permission, UserPermission
from apps.permissions.services.permissions import PermissionService

User = get_user_model()


class Command(BaseCommand):
    help = 'Adds all existing permissions to a specified user'

    def add_arguments(self, parser):
        # Required arguments
        parser.add_argument('user_identifier', type=str, help='User identifier (vekalat_id, email, or phone_number)')

        # Optional arguments
        parser.add_argument(
            '--remove',
            action='store_true',
            help='Remove all permissions instead of adding them',
        )

    def handle(self, *args, **options):
        user_identifier = options['user_identifier']
        remove_mode = options.get('remove', False)

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

        # Get all active permissions
        permissions = Permission.objects.filter(is_active=True)

        if remove_mode:
            # Remove all permissions
            deleted_count, _ = UserPermission.objects.filter(user=user).delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully removed {deleted_count} permissions from user "{user.get_full_name()}" ({user_identifier})')
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
                self.style.SUCCESS(f'Successfully added {added_count} permissions to user "{user.get_full_name()}" ({user_identifier})')
            )