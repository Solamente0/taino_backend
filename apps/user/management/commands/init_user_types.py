from django.core.management.base import BaseCommand
from apps.authentication.models import UserType


class Command(BaseCommand):
    help = "Initialize user types/roles in the system"

    def handle(self, *args, **options):
        user_types = [
            {"name": "وکیل", "static_name": "lawyer", "description": "کاربر با دسترسی وکیل"},
            {"name": "موکل", "static_name": "client", "description": "موکل وکیل"},
            {"name": "کاربر عادی", "static_name": "public_user", "description": "کاربر عادی"},
            {"name": "منشی", "static_name": "secretary", "description": "منشی وکیل"},
            {"name": "شخص حقوقی", "static_name": "legal_entity", "description": "شخصیت حقوقی"},
            {"name": "ادمین کانون", "static_name": "bar_lawyer", "description": "شخصیت مدیر کانون"},
            {"name": "مقام قضائی", "static_name": "judicial_authority", "description": "شخصیت مقام قضائی"},
            {"name": "کارشناس", "static_name": "court_expert", "description": "شخصیت کارشناس قضائی"},
        ]

        for user_type_data in user_types:
            user_type, created = UserType.objects.update_or_create(
                static_name=user_type_data["static_name"],
                defaults={"name": user_type_data["name"], "description": user_type_data["description"], "is_active": True},
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created user type: {user_type.name}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Updated user type: {user_type.name}"))
