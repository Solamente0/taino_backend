import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
from apps.country.models import Country, State, City


class Command(BaseCommand):
    help = "Delete all states and cities, reset sequences, and recreate from JSON fixture"

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Confirm deletion of all states and cities",
        )

    def handle(self, *args, **options):
        confirm = options.get("confirm", False)

        if not confirm:
            self.stdout.write(self.style.ERROR("=" * 60))
            self.stdout.write(self.style.ERROR("WARNING: This will DELETE ALL states and cities!"))
            self.stdout.write(self.style.ERROR("=" * 60))
            self.stdout.write(self.style.WARNING("\nThis command will:"))
            self.stdout.write("  1. Delete all City records")
            self.stdout.write("  2. Delete all State records")
            self.stdout.write("  3. Reset database sequences")
            self.stdout.write("  4. Recreate states and cities from fixture\n")

            # Show current counts
            city_count = City.global_objects.count()
            state_count = State.global_objects.count()
            self.stdout.write(self.style.WARNING(f"Current counts:"))
            self.stdout.write(f"  - States: {state_count}")
            self.stdout.write(f"  - Cities: {city_count}\n")

            self.stdout.write(self.style.ERROR("To proceed, run with --confirm flag:"))
            self.stdout.write(self.style.ERROR("python manage.py reset_iran_cities --confirm\n"))
            return

        # Path to the fixture file
        fixture_path = os.path.join(settings.BASE_DIR, "apps", "country", "fixtures", "cities", "IR.json")

        # Check if file exists
        if not os.path.exists(fixture_path):
            self.stdout.write(self.style.ERROR(f"Fixture file not found: {fixture_path}"))
            return

        # Load JSON data
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Get Iran country
        try:
            country = Country.global_objects.get(code="IR")
        except Country.DoesNotExist:
            # Create Iran country if it doesn't exist
            country = Country.global_objects.create(
                code="IR",
                name="جمهوری اسلامی ایران",
                dial_code="98",
                is_active=True,
                is_sms_enabled=True,
            )
            self.stdout.write(self.style.SUCCESS(f"Created country: {country.name}"))

        # Step 1: Delete all cities
        self.stdout.write("\nStep 1: Deleting all cities...")
        city_count = City.global_objects.count()
        City.global_objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"  Deleted {city_count} cities"))

        # Step 2: Delete all states
        self.stdout.write("\nStep 2: Deleting all states...")
        state_count = State.global_objects.count()
        State.global_objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"  Deleted {state_count} states"))

        # Step 3: Reset sequences
        self.stdout.write("\nStep 3: Resetting database sequences...")
        with connection.cursor() as cursor:
            # Get table names
            state_table = State._meta.db_table
            city_table = City._meta.db_table

            # Reset sequences (PostgreSQL)
            try:
                cursor.execute(f"ALTER SEQUENCE {state_table}_id_seq RESTART WITH 1;")
                self.stdout.write(self.style.SUCCESS(f"  Reset {state_table} sequence"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  Could not reset {state_table} sequence: {e}"))

            try:
                cursor.execute(f"ALTER SEQUENCE {city_table}_id_seq RESTART WITH 1;")
                self.stdout.write(self.style.SUCCESS(f"  Reset {city_table} sequence"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  Could not reset {city_table} sequence: {e}"))

        # Step 4: Create states and cities from fixture
        self.stdout.write("\nStep 4: Creating states and cities from fixture...")

        provinces = data.get("provinces", [])
        total_provinces = 0
        total_cities = 0

        for province_data in provinces:
            fa_name = province_data.get("fa_name")

            if not fa_name:
                continue

            # Create state
            state = State.global_objects.create(
                name=fa_name,
                country=country,
                is_active=True,
            )
            total_provinces += 1
            self.stdout.write(self.style.SUCCESS(f"  Created province: {fa_name}"))

            # Create cities for this province
            cities = province_data.get("cities", [])

            for city_data in cities:
                city_fa_name = city_data.get("fa_name")

                if not city_fa_name:
                    continue

                City.global_objects.create(
                    name=city_fa_name,
                    state=state,
                    country=country,
                    is_active=True,
                )
                total_cities += 1

        # Summary
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("Reset completed successfully!"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS(f"Created provinces: {total_provinces}"))
        self.stdout.write(self.style.SUCCESS(f"Created cities: {total_cities}"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
