# apps/subscription/management/commands/load_subscription_data.py
import os
import json
import logging
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from apps.subscription.models import Package

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Load subscription package data from fixtures"

    def handle(self, *args, **options):
        fixtures_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "fixtures",
            "packages.json"
        )

        self.stdout.write(self.style.NOTICE(f"Loading subscription data from {fixtures_path}"))

        try:
            if not os.path.exists(fixtures_path):
                self.stdout.write(self.style.ERROR(f"Fixture file does not exist: {fixtures_path}"))
                return

            with open(fixtures_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            self._load_packages(data)

            self.stdout.write(self.style.SUCCESS("Successfully loaded subscription data"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error loading subscription data: {str(e)}"))
            logger.exception("Error loading subscription data")
            raise

    @transaction.atomic
    def _load_packages(self, data):
        """Load package data from fixtures"""
        packages_count = 0
        packages_updated = 0

        for item in data:
            if item["model"] != "subscription.package":
                continue

            try:
                fields = item["fields"]
                pid = fields.pop("pid")

                # Try to get existing package or create new one
                try:
                    package = Package.objects.get(pid=pid)
                    # Update existing package
                    for key, value in fields.items():
                        setattr(package, key, value)
                    package.save()
                    packages_updated += 1
                    self.stdout.write(self.style.WARNING(f"Updated package: {package.name}"))
                except ObjectDoesNotExist:
                    # Create new package
                    fields["pid"] = pid
                    package = Package.objects.create(**fields)
                    packages_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Created new package: {package.name}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing package: {str(e)}"))
                logger.exception("Error processing package")
                raise

        self.stdout.write(self.style.SUCCESS(
            f"Processed packages: {packages_count} created, {packages_updated} updated"
        ))
