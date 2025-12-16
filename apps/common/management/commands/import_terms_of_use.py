from django.core.management.base import BaseCommand
from apps.common.models import TermsOfUse
from django.db import transaction
import os
import json
from django.conf import settings


class Command(BaseCommand):
    help = "Populates the database with comprehensive terms of use for an online legal service platform"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force update existing terms (will deactivate all existing terms first)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without making database changes",
        )
        parser.add_argument(
            "--file",
            type=str,
            default="fixtures/terms_of_use.json",
            help="Path to the JSON file containing terms of use (relative to project root)",
        )

    def handle(self, *args, **options):
        force_update = options.get("force", False)
        dry_run = options.get("dry_run", False)
        json_file = options.get("file", "fixtures/terms_of_use.json")

        # Load terms data from JSON file
        terms_data = self.get_terms_of_use(json_file)

        if not terms_data:
            self.stdout.write(
                self.style.ERROR("No terms of use data found. Please check the JSON file.")
            )
            return

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No database changes will be made"))
            for term in terms_data:
                self.stdout.write(f"Would create: {term['title']}")
                if "children" in term and term["children"]:
                    for child in term["children"]:
                        self.stdout.write(f"  - {child['title']}")
            return

        # Use transaction to ensure atomicity
        with transaction.atomic():
            if force_update:
                # Deactivate all existing terms
                count = TermsOfUse.objects.all().update(is_active=False)
                self.stdout.write(self.style.WARNING(f"Deactivated {count} existing terms of use"))

            # Create new terms
            created_count = 0
            updated_count = 0

            for order, term_data in enumerate(terms_data, start=1):
                term, created = self._create_or_update_term(None, term_data, order)

                if created:
                    created_count += 1
                else:
                    updated_count += 1

                # Handle children if any
                if "children" in term_data and term_data["children"]:
                    for child_order, child_data in enumerate(term_data["children"], start=1):
                        child, child_created = self._create_or_update_term(term, child_data, child_order)
                        if child_created:
                            created_count += 1
                        else:
                            updated_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Operation completed: {created_count} terms created, {updated_count} terms updated"
                )
            )

            # Count total active terms
            active_count = TermsOfUse.objects.filter(is_active=True).count()
            total_count = TermsOfUse.objects.count()
            self.stdout.write(
                self.style.SUCCESS(f"Total terms in database: {total_count} ({active_count} active)")
            )

    def _create_or_update_term(self, parent, term_data, order):
        """Create or update a single term of use"""
        # Look for existing term with same title
        existing = TermsOfUse.objects.filter(title=term_data["title"], parent=parent).first()

        if existing:
            # Update existing term
            existing.content = term_data["content"]
            existing.order = order
            existing.is_active = True
            existing.save()
            self.stdout.write(self.style.SUCCESS(f"Updated term: {term_data['title']}"))
            return existing, False
        else:
            # Create new term
            term = TermsOfUse.objects.create(
                title=term_data["title"],
                content=term_data["content"],
                order=order,
                parent=parent,
                is_active=True,
            )
            self.stdout.write(self.style.SUCCESS(f"Created term: {term_data['title']}"))
            return term, True

    def get_terms_of_use(self, json_file_path):
        """
        Load terms of use data from JSON file
        If the file doesn't exist, return an empty list
        """
        # Path is relative to the project root
        fixture_path = os.path.join(settings.BASE_DIR, json_file_path)

        # Check if file exists
        if not os.path.exists(fixture_path):
            self.stdout.write(
                self.style.WARNING(f"Fixture file not found at {fixture_path}. Please create it first.")
            )
            return []

        try:
            # Load JSON data
            with open(fixture_path, 'r', encoding='utf-8') as file:
                terms_data = json.load(file)

            # Return the loaded data
            return terms_data
        except json.JSONDecodeError:
            self.stdout.write(
                self.style.ERROR(f"Invalid JSON format in {fixture_path}. Please check the file.")
            )
            return []
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error loading terms of use: {str(e)}")
            )
            return []