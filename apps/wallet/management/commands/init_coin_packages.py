# apps/wallet/management/commands/init_coin_packages.py

from django.core.management.base import BaseCommand
from apps.wallet.models import CoinPackage
from apps.authentication.models import UserType


class Command(BaseCommand):
    help = "Initialize default coin packages for different user roles"

    def handle(self, *args, **options):
        # Get user roles
        try:
            lawyer_role = UserType.objects.get(static_name="lawyer")
            client_role = UserType.objects.get(static_name="client")
        except UserType.DoesNotExist:
            self.stdout.write(
                self.style.ERROR("User roles not found. Please run init_user_types first.")
            )
            return

        # Generic packages (for all users)
        generic_packages = [
            {
                "value": 10,
                "label": "پکیج مقدماتی",
                "price": 25000,
                "order": 1,
                "description": "مناسب برای استفاده‌های ساده",
                "role": None
            },
            {
                "value": 50,
                "label": "پکیج برنزی",
                "price": 100000,
                "order": 2,
                "description": "مناسب برای استفاده متوسط",
                "role": None
            },
            {
                "value": 100,
                "label": "پکیج نقره‌ای",
                "price": 180000,
                "order": 3,
                "description": "10% تخفیف - مناسب برای استفاده زیاد",
                "role": None
            },
        ]

        # Lawyer-specific packages (better prices)
        lawyer_packages = [
            {
                "value": 100,
                "label": "پکیج ویژه وکیل",
                "price": 150000,
                "order": 1,
                "description": "تخفیف ویژه وکلا - 25% تخفیف",
                "role": lawyer_role
            },
            {
                "value": 500,
                "label": "پکیج طلایی وکیل",
                "price": 650000,
                "order": 2,
                "description": "تخفیف ویژه وکلا - 35% تخفیف",
                "role": lawyer_role
            },
            {
                "value": 1000,
                "label": "پکیج پلاتینیوم وکیل",
                "price": 1100000,
                "order": 3,
                "description": "تخفیف ویژه وکلا - 45% تخفیف",
                "role": lawyer_role
            },
        ]

        # Client-specific packages
        client_packages = [
            {
                "value": 20,
                "label": "پکیج موکل",
                "price": 45000,
                "order": 1,
                "description": "مناسب برای مشاوره‌های اولیه",
                "role": client_role
            },
            {
                "value": 50,
                "label": "پکیج ویژه موکل",
                "price": 100000,
                "order": 2,
                "description": "مناسب برای مشاوره‌های کامل",
                "role": client_role
            },
        ]

        all_packages = generic_packages + lawyer_packages + client_packages

        for package_data in all_packages:
            role_str = f" ({package_data['role'].name})" if package_data['role'] else " (عمومی)"
            
            package, created = CoinPackage.objects.update_or_create(
                label=package_data["label"],
                role=package_data["role"],
                defaults={
                    "value": package_data["value"],
                    "price": package_data["price"],
                    "order": package_data["order"],
                    "description": package_data["description"],
                    "is_active": True,
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created package: {package.label}{role_str} - {package.value} coins for {package.price} Rials"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Updated package: {package.label}{role_str} - {package.value} coins for {package.price} Rials"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSuccessfully initialized {len(all_packages)} coin packages!"
            )
        )
