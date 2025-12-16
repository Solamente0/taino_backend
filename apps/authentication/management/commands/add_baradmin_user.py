from django.core.management.base import BaseCommand
from apps.authentication.models import UserType


class Command(BaseCommand):
    help = 'ایجاد نقش bar_admin برای مدیران کانون وکلا'

    def handle(self, *args, **options):
        try:
            # ایجاد یا به‌روزرسانی نقش bar_admin
            bar_admin_role, created = UserType.objects.update_or_create(
                static_name='bar_admin',
                defaults={
                    'name': 'مدیر کانون',
                    'description': 'مدیر کانون وکلا - دسترسی به مدیریت کاربران موقت و وکلای کانون',
                    'is_active': True
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ نقش "{bar_admin_role.name}" با موفقیت ایجاد شد')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'! نقش "{bar_admin_role.name}" از قبل وجود داشت و به‌روزرسانی شد')
                )

            # نمایش اطلاعات نقش
            self.stdout.write(self.style.SUCCESS(f'\nاطلاعات نقش:'))
            self.stdout.write(f'  - PID: {bar_admin_role.pid}')
            self.stdout.write(f'  - Static Name: {bar_admin_role.static_name}')
            self.stdout.write(f'  - Name: {bar_admin_role.name}')
            self.stdout.write(f'  - Description: {bar_admin_role.description}')
            self.stdout.write(f'  - Is Active: {bar_admin_role.is_active}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ خطا در ایجاد نقش bar_admin: {str(e)}')
            )
            raise
