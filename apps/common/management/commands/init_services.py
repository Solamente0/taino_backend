from django.core.management.base import BaseCommand
from django.db import transaction
from apps.common.models import ServiceItem


class Command(BaseCommand):
    help = "Initialize default service items for the application"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force update existing services",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Perform a dry run without making database changes",
        )
        parser.add_argument(
            "--disable-all",
            action="store_true",
            help="Disable all existing services before creating new ones",
        )

    def handle(self, *args, **options):
        force_update = options.get("force", False)
        dry_run = options.get("dry_run", False)
        disable_all = options.get("disable_all", False)

        # Define all the service items to create
        services = [
            {
                "static_name": "lawyer_chat",
                "name": "گفتگو با وکیل",
                "description": "گفتگوی مستقیم با وکلای مجرب در زمینه‌های مختلف حقوقی",
                # "icon": "chat-bubble",
                "icon": None,
                "order": 10,
            },
            {
                "static_name": "iran_justice",
                "name": "عدل ایران",
                "description": "دسترسی به قوانین، رویه قضایی و منابع حقوقی",
                # "icon": "scale-balance",
                "icon": None,
                "order": 20,
            },
            {
                "static_name": "archive",
                "name": "بایگانی",
                "description": "بایگانی و مدیریت پرونده‌های حقوقی",
                # "icon": "folder-archive",
                "icon": None,
                "order": 30,
            },
            {
                "static_name": "objections",
                "name": "اعتراضات",
                "description": "ثبت و پیگیری اعتراضات قضایی",
                # "icon": "gavel",
                "icon": None,
                "order": 40,
            },
            {
                "static_name": "document_exchange",
                "name": "تبادل لوایح",
                "description": "تبادل لوایح و اسناد حقوقی به صورت الکترونیکی",
                # "icon": "document-exchange",
                "icon": None,
                "order": 50,
            },
            {
                "static_name": "session_registration",
                "name": "ثبت جلسات",
                "description": "ثبت و مدیریت جلسات دادگاه و مشاوره حقوقی",
                # "icon": "calendar-check",
                "icon": None,
                "order": 60,
            },
            {
                "static_name": "v",
                "name": "وی",
                "description": "خدمات پایه وکالت آنلاین",
                # "icon": "v-logo",
                "icon": None,
                "order": 70,
            },
            {
                "static_name": "v_plus",
                "name": "وی +",
                "description": "خدمات پیشرفته وکالت آنلاین با امکانات بیشتر",
                # "icon": "v-plus-logo",
                "icon": None,
                "order": 80,
            },
            {
                "static_name": "v_x",
                "name": "وی ایکس",
                "description": "بسته ویژه و کامل خدمات وکالت آنلاین",
                # "icon": "v-premium-logo",
                "icon": None,
                "order": 90,
            },
        ]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No database changes will be made"))

            # Show what would be created or updated
            for service_data in services:
                existing = ServiceItem.objects.filter(static_name=service_data["static_name"]).first()

                if existing:
                    if force_update:
                        self.stdout.write(f"Would update: {service_data['name']} ({service_data['static_name']})")
                    else:
                        self.stdout.write(f"Would skip: {service_data['name']} (already exists)")
                else:
                    self.stdout.write(f"Would create: {service_data['name']} ({service_data['static_name']})")

            return

        # Use transaction to ensure atomicity
        with transaction.atomic():
            if disable_all:
                # Disable all existing services
                count = ServiceItem.objects.update(is_active=False)
                self.stdout.write(self.style.WARNING(f"Disabled {count} existing services"))

            # Create or update each service
            created_count = 0
            updated_count = 0
            skipped_count = 0

            for service_data in services:
                existing = ServiceItem.objects.filter(static_name=service_data["static_name"]).first()

                if existing and not force_update:
                    self.stdout.write(f"Skipping: {service_data['name']} (already exists)")
                    skipped_count += 1
                    continue

                service, created = ServiceItem.objects.update_or_create(
                    static_name=service_data["static_name"],
                    defaults={
                        "name": service_data["name"],
                        "description": service_data["description"],
                        "icon": service_data["icon"],
                        "order": service_data["order"],
                        "is_active": True,
                    },
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created service: {service.name}"))
                    created_count += 1
                else:
                    self.stdout.write(self.style.SUCCESS(f"Updated service: {service.name}"))
                    updated_count += 1

            # Final summary
            self.stdout.write(
                self.style.SUCCESS(
                    f"Operation completed: {created_count} created, {updated_count} updated, {skipped_count} skipped"
                )
            )

            # Count total active services
            active_count = ServiceItem.objects.filter(is_active=True).count()
            total_count = ServiceItem.objects.count()
            self.stdout.write(self.style.SUCCESS(f"Total services in database: {total_count} ({active_count} active)"))
