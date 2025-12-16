import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q
from django.db import transaction
from apps.country.models import Country, State, City


class Command(BaseCommand):
    help = 'Load Iran provinces and cities from JSON fixture'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating',
        )
        parser.add_argument(
            '--delete-duplicates',
            action='store_true',
            help='Delete English duplicate cities if Persian version exists',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        delete_duplicates = options.get('delete_duplicates', False)

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )

        if delete_duplicates:
            self.stdout.write(
                self.style.WARNING('DUPLICATE DELETION MODE - Will delete English duplicates')
            )

        # Path to the fixture file
        fixture_path = os.path.join(
            settings.BASE_DIR,
            'apps',
            'country',
            'fixtures',
            'cities',
            'IR.json'
        )

        # Check if file exists
        if not os.path.exists(fixture_path):
            self.stdout.write(
                self.style.ERROR(f'Fixture file not found: {fixture_path}')
            )
            return

        # Load JSON data
        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Get or create Iran country
        country, created = Country.objects.get_or_create(
            code='IR',
            defaults={
                'name': 'جمهوری اسلامی ایران',
                'dial_code': '98',
                'is_active': True,
                'is_sms_enabled': True,
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created country: {country.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Country already exists: {country.name}')
            )

        # Process provinces and cities
        provinces = data.get('provinces', [])

        total_provinces = len(provinces)
        total_cities = 0
        created_provinces = 0
        updated_provinces = 0
        created_cities = 0
        updated_cities = 0
        skipped_cities = 0
        deleted_duplicates = 0

        for province_data in provinces:
            fa_name = province_data.get('fa_name')
            us_name = province_data.get('us_name')

            if not fa_name:
                continue

            # Check if state exists with either fa_name or us_name
            state = State.objects.filter(
                Q(name=fa_name) | Q(name=us_name),
                country=country
            ).first()

            if state:
                # Update existing state with fa_name
                if state.name != fa_name:
                    old_name = state.name
                    if not dry_run:
                        state.name = fa_name
                        state.save()
                    self.stdout.write(
                        self.style.WARNING(
                            f'  {"[DRY RUN] Would update" if dry_run else "Updated"} province: {old_name} -> {fa_name}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  Province already exists: {fa_name}')
                    )
                updated_provinces += 1
            else:
                # Create new state
                if not dry_run:
                    state = State.objects.create(
                        name=fa_name,
                        country=country,
                        is_active=True,
                    )
                    created_provinces += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  Created province: {fa_name}')
                    )
                else:
                    # For dry run, we still need to check cities, so create a temporary state
                    created_provinces += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  [DRY RUN] Would create province: {fa_name}')
                    )
                    # Skip city processing for non-existent states in dry-run
                    continue

            # Process cities for this province
            cities = province_data.get('cities', [])

            for city_data in cities:
                city_fa_name = city_data.get('fa_name')
                city_us_name = city_data.get('us_name')

                if not city_fa_name:
                    continue

                total_cities += 1

                # Check if Persian version already exists with correct state
                persian_city = City.objects.filter(
                    name=city_fa_name,
                    state=state,
                    country=country
                ).first()

                # Check if English version exists
                english_city = City.objects.filter(
                    name=city_us_name,
                    country=country
                ).first()

                if persian_city and english_city:
                    # Both exist - delete English duplicate
                    if delete_duplicates:
                        if not dry_run:
                            english_city.delete()
                            self.stdout.write(
                                self.style.ERROR(
                                    f'    Deleted duplicate: {city_us_name} (Persian version exists: {city_fa_name})'
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'    [DRY RUN] Would delete duplicate: {city_us_name} (Persian version exists: {city_fa_name})'
                                )
                            )
                        deleted_duplicates += 1
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f'    WARNING: Duplicate found - {city_us_name} and {city_fa_name} both exist. Use --delete-duplicates to clean up.'
                            )
                        )
                    skipped_cities += 1
                    continue

                if persian_city:
                    # Persian version exists and is correct
                    skipped_cities += 1
                    continue

                # Find city by either name
                city = City.objects.filter(
                    Q(name=city_fa_name) | Q(name=city_us_name),
                    country=country
                ).first()

                if city:
                    # Check if city needs updates
                    needs_update = False
                    updates = []

                    if city.name != city_fa_name:
                        needs_update = True
                        updates.append(f"name: {city.name} -> {city_fa_name}")

                    # Compare state by ID or None
                    current_state_id = city.state.id if city.state else None
                    target_state_id = state.id if state else None

                    if current_state_id != target_state_id:
                        needs_update = True
                        state_old = city.state.name if city.state else "None"
                        state_new = state.name
                        updates.append(f"state: {state_old} -> {state_new}")

                    if needs_update:
                        if not dry_run:
                            try:
                                with transaction.atomic():
                                    city.name = city_fa_name
                                    city.state = state
                                    city.save()
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f'    Updated city: {" | ".join(updates)}'
                                        )
                                    )
                                    updated_cities += 1
                            except Exception as e:
                                self.stdout.write(
                                    self.style.ERROR(
                                        f'    ERROR updating city: {" | ".join(updates)} - {str(e)}'
                                    )
                                )
                                skipped_cities += 1
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'    [DRY RUN] Would update city: {" | ".join(updates)}'
                                )
                            )
                            updated_cities += 1
                    else:
                        skipped_cities += 1
                else:
                    # Create new city
                    if not dry_run:
                        try:
                            City.objects.create(
                                name=city_fa_name,
                                state=state,
                                country=country,
                                is_active=True,
                            )
                            self.stdout.write(
                                self.style.SUCCESS(f'    Created city: {city_fa_name}')
                            )
                            created_cities += 1
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f'    ERROR creating city {city_fa_name}: {str(e)}')
                            )
                            skipped_cities += 1
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'    [DRY RUN] Would create city: {city_fa_name}'
                            )
                        )
                        created_cities += 1

        # Summary
        self.stdout.write(
            self.style.SUCCESS('\n' + '='*60)
        )
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN COMPLETED - No changes were made')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Import completed successfully!')
            )
        self.stdout.write(
            self.style.SUCCESS(f'Total provinces processed: {total_provinces}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'  - Created: {created_provinces}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'  - Updated/Already existed: {updated_provinces}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Total cities processed: {total_cities}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'  - Created: {created_cities}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'  - Updated: {updated_cities}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'  - Already correct: {skipped_cities}')
        )
        if delete_duplicates:
            self.stdout.write(
                self.style.SUCCESS(f'  - Deleted duplicates: {deleted_duplicates}')
            )
        self.stdout.write(
            self.style.SUCCESS('='*60)
        )
