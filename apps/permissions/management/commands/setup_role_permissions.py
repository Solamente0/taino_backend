import json
import os
import sys
from django.core.management.base import BaseCommand
from apps.permissions.models import Permission, PermissionCategory, UserTypePermission
from apps.authentication.models import UserType
from django.conf import settings


class Command(BaseCommand):
    help = "ایجاد دسترسی‌های سیستم بر اساس نقش‌های کاربری از فایل JSON"

    def add_arguments(self, parser):
        parser.add_argument("--file", help="مسیر فایل JSON حاوی دسترسی‌ها")
        parser.add_argument("--create-sample", action="store_true", help="ایجاد فایل نمونه JSON دسترسی‌ها")

    def handle(self, *args, **kwargs):
        # بررسی آرگومان ایجاد فایل نمونه
        if kwargs.get("create_sample"):
            sample_path = os.path.join(settings.BASE_DIR, "apps/permissions/fixtures/role_permissions.json")
            # self._create_sample_file(sample_path)
            # self.stdout.write(self.style.SUCCESS(f"فایل نمونه در مسیر {sample_path} ایجاد شد."))
            return

        self.stdout.write(self.style.SUCCESS("شروع ایجاد دسترسی‌ها از فایل JSON..."))

        # خواندن فایل JSON
        json_file = kwargs.get("file")

        if json_file:
            # تعیین مسیر کامل فایل
            if not os.path.isabs(json_file):
                json_file = os.path.join(settings.BASE_DIR, json_file)

            try:
                with open(json_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
            except FileNotFoundError:
                self.stdout.write(self.style.ERROR(f"فایل {json_file} یافت نشد!"))
                return
            except json.JSONDecodeError as e:
                self.stdout.write(self.style.ERROR(f"خطا در خواندن فایل JSON: {str(e)}"))
                return
        else:
            # اگر فایل مشخص نشده باشد، از داده‌های پیش‌فرض استفاده می‌کنیم
            self.stdout.write(self.style.WARNING("فایل JSON مشخص نشده است. از داده‌های پیش‌فرض استفاده می‌شود."))
            # data = get_sample_json_content()

        # ایجاد دسته‌بندی‌ها
        categories = {}
        for category_data in data.get("categories", []):
            category = self._create_category(category_data["name"], category_data.get("description", ""))
            categories[category_data["name"]] = category

        # ایجاد دسترسی‌ها
        created_permissions = []
        for permission_data in data.get("permissions", []):
            category = categories.get(permission_data["category"])
            if not category:
                self.stdout.write(
                    self.style.WARNING(
                        f'دسته‌بندی "{permission_data["category"]}" برای دسترسی "{permission_data["name"]}" یافت نشد!'
                    )
                )
                continue

            permission, created = Permission.objects.get_or_create(
                code_name=permission_data["code_name"], defaults={"name": permission_data["name"], "category": category}
            )

            if created:
                created_permissions.append(permission)
                self.stdout.write(f'دسترسی "{permission_data["name"]}" ایجاد شد.')
            else:
                permission.name = permission_data["name"]
                permission.category = category
                permission.save()
                self.stdout.write(f'دسترسی "{permission_data["name"]}" به‌روزرسانی شد.')

        # ایجاد نقش‌ها
        roles = {}
        for role_data in data.get("roles", []):
            role, created = UserType.objects.get_or_create(
                static_name=role_data["static_name"],
                defaults={"name": role_data["name"], "description": role_data.get("description", "")},
            )
            if created:
                self.stdout.write(f'نقش "{role_data["name"]}" ایجاد شد.')
            roles[role_data["static_name"]] = role

        # تخصیص دسترسی‌ها به نقش‌ها
        for role_data in data.get("roles", []):
            role = roles.get(role_data["static_name"])
            permissions = role_data.get("permissions", [])
            self._assign_permissions_to_role(role, permissions)

        self.stdout.write(self.style.SUCCESS("همه دسترسی‌ها با موفقیت ایجاد شدند."))

    def _create_category(self, name, description):
        """ایجاد یا به‌روزرسانی دسته‌بندی دسترسی‌ها"""
        category, created = PermissionCategory.objects.get_or_create(name=name, defaults={"description": description})
        if created:
            self.stdout.write(f'دسته‌بندی "{name}" ایجاد شد.')
        return category

    def _assign_permissions_to_role(self, role, permission_codes):
        """تخصیص دسترسی‌ها به یک نقش"""
        # حذف دسترسی‌های قبلی نقش
        UserTypePermission.objects.filter(user_type=role).delete()

        # اضافه کردن دسترسی‌های جدید
        for code in permission_codes:
            try:
                permission = Permission.objects.get(code_name=code)
                UserTypePermission.objects.create(user_type=role, permission=permission)
                self.stdout.write(f'دسترسی "{code}" به نقش "{role.name}" اضافه شد.')
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'دسترسی با کد "{code}" یافت نشد.'))

    #
    # def _create_sample_file(self, file_path):
    #     """ایجاد فایل نمونه JSON برای دسترسی‌ها"""
    #     # sample_data = get_sample_json_content()
    #
    #     try:
    #         with open(file_path, "w", encoding="utf-8") as file:
    #             json.dump(sample_data, file, ensure_ascii=False, indent=4)
    #         self.stdout.write(self.style.SUCCESS(f"فایل نمونه JSON در مسیر {file_path} ایجاد شد."))
    #     except Exception as e:
    #         self.stdout.write(self.style.ERROR(f"خطا در ایجاد فایل نمونه: {str(e)}"))
