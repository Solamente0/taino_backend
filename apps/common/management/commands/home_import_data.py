import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.document.models import TainoDocument
from pathlib import Path

from apps.document.models import TainoDocument
from apps.common.models import HomePage, HeroSectionImage, PartnerShip, WayToFileTax, Service, TeamMember, Testimonial


class Command(BaseCommand):
    help = "Import homepage data from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument("json_file", type=str, help="Path to the JSON file")

    def handle(self, *args, **options):
        json_file_path = options["json_file"]

        if not os.path.exists(json_file_path):
            self.stderr.write(self.style.ERROR(f"File not found: {json_file_path}"))
            return

        try:
            with open(json_file_path, "r") as file:
                data = json.load(file)

            if not data.get("status") or not data.get("data"):
                self.stderr.write(self.style.ERROR("Invalid JSON format"))
                return

            home_data = data["data"]

            with transaction.atomic():
                # Create or update HomePage
                self.import_home_page(home_data)

            self.stdout.write(self.style.SUCCESS("Successfully imported home page data"))

        except json.JSONDecodeError:
            self.stderr.write(self.style.ERROR("Invalid JSON file"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error importing data: {str(e)}"))

    def import_home_page(self, home_data):
        # Get or create HomePage
        home_page, created = HomePage.objects.get_or_create(pk=1)

        # Update basic fields
        home_page.header_title = home_data.get("header_title", "")
        home_page.header_sub_title = home_data.get("header_Sub_title_", "")
        home_page.why = home_data.get("why", "")
        home_page.why_point1 = home_data.get("why_point1", "")
        home_page.why_point2 = home_data.get("why_point2", "")
        home_page.why_point3 = home_data.get("why_point3", "")
        home_page.why_point4 = home_data.get("why_point4", "")
        home_page.how_to_file_tax_title = home_data.get("how_to_file_tax_title", "")
        home_page.how_to_file_tax_short_description = home_data.get("how_to_file_tax_short_description", "")

        # Handle corporate strategy
        corporate_strategy = home_data.get("corporate_strategy", {})
        if corporate_strategy:
            # Get or create TainoDocument for corporate_strategy_img
            img_url = corporate_strategy.get("img1", "")
            if img_url:
                doc, _ = self._get_or_create_document(img_url)
                home_page.corporate_strategy_img = doc

            home_page.corporate_strategy_title = corporate_strategy.get("title", "")
            home_page.corporate_strategy_description = corporate_strategy.get("description", "")
            home_page.corporate_strategy_section1 = corporate_strategy.get("section1", "")
            home_page.corporate_strategy_section1_des = corporate_strategy.get("section1_des", "")
            home_page.corporate_strategy_section2 = corporate_strategy.get("section2", "")
            home_page.corporate_strategy_section2_des = corporate_strategy.get("section2_des", "")

        home_page.save()
        self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Updated"} home page'))

        # Import related models
        self._import_hero_section_images(home_page, home_data.get("hero_section_images", []))
        self._import_partnerships(home_page, home_data.get("partner_ships", []))
        self._import_ways_to_file_tax(home_page, home_data.get("way_to_file_tax", []))
        self._import_services(home_page, home_data.get("services", []))
        self._import_team_members(home_data.get("team_members", {}))
        self._import_testimonials(home_data.get("testimonials", []))

    def _get_or_create_document(self, url):
        """Helper to get or create an TainoDocument from a URL"""
        filename = Path(url).name
        doc, created = TainoDocument.objects.get_or_create(
            file_url=url, defaults={"name": filename, "file_type": self._get_file_type(filename), "file_path": url}
        )
        return doc, created

    def _get_file_type(self, filename):
        """Helper to determine file type from filename"""
        ext = filename.split(".")[-1].lower()
        if ext in ["jpg", "jpeg", "png", "gif"]:
            return "image"
        elif ext in ["pdf"]:
            return "pdf"
        elif ext in ["doc", "docx"]:
            return "document"
        return "other"

    def _import_hero_section_images(self, home_page, image_urls):
        """Import hero section images"""
        # Clear existing images
        HeroSectionImage.objects.filter(home_page=home_page).delete()

        for i, url in enumerate(image_urls):
            doc, _ = self._get_or_create_document(url)
            HeroSectionImage.objects.create(home_page=home_page, image=doc, order=i)

        self.stdout.write(self.style.SUCCESS(f"Imported {len(image_urls)} hero section images"))

    def _import_partnerships(self, home_page, image_urls):
        """Import partnerships"""
        # Clear existing partnerships
        PartnerShip.objects.filter(home_page=home_page).delete()

        for i, url in enumerate(image_urls):
            doc, _ = self._get_or_create_document(url)
            PartnerShip.objects.create(home_page=home_page, image=doc, order=i)

        self.stdout.write(self.style.SUCCESS(f"Imported {len(image_urls)} partnerships"))

    def _import_ways_to_file_tax(self, home_page, ways_data):
        """Import ways to file tax"""
        # Clear existing ways
        WayToFileTax.objects.filter(home_page=home_page).delete()

        for i, way in enumerate(ways_data):
            img_url = way.get("image", "")
            doc, _ = self._get_or_create_document(img_url)

            WayToFileTax.objects.create(
                home_page=home_page,
                title=way.get("title", ""),
                description=way.get("description", ""),
                image=doc,
                order=i,
                is_active=True,
            )

        self.stdout.write(self.style.SUCCESS(f"Imported {len(ways_data)} ways to file tax"))

    def _import_services(self, home_page, services_data):
        """Import services"""
        # Clear existing services
        Service.objects.filter(home_page=home_page).delete()

        for i, service in enumerate(services_data):
            logo_url = service.get("logo", "")
            doc, _ = self._get_or_create_document(logo_url)

            Service.objects.create(
                home_page=home_page,
                title=service.get("title", ""),
                description=service.get("description", ""),
                logo=doc,
                order=i,
                is_active=True,
            )

        self.stdout.write(self.style.SUCCESS(f"Imported {len(services_data)} services"))

    def _import_team_members(self, team_data):
        """Import team members"""
        if not team_data:
            return

        # Clear existing team members
        TeamMember.objects.all().delete()

        # Import executive team
        exec_team = team_data.get("executive_team", [])
        for i, member in enumerate(exec_team):
            user_data = member.get("user", {})
            image_url = user_data.get("image", "")
            doc = None
            if image_url:
                doc, _ = self._get_or_create_document(image_url)

            TeamMember.objects.create(
                team_type="executive_team",
                first_name=user_data.get("first_name", ""),
                last_name=user_data.get("last_name", ""),
                title=member.get("title", ""),
                university=member.get("university", ""),
                short_brief=user_data.get("short_brief", ""),
                image=doc,
                linkedin=user_data.get("linkedIn", ""),
                twitter=user_data.get("twitter", ""),
                facebook=user_data.get("facebook", ""),
                order=i,
                is_active=True,
            )

        # Import accounting affiliates
        affiliates = team_data.get("accounting_affiliates", [])
        for i, member in enumerate(affiliates):
            user_data = member.get("user", {})
            image_url = user_data.get("image", "")
            doc = None
            if image_url:
                doc, _ = self._get_or_create_document(image_url)

            TeamMember.objects.create(
                team_type="accounting_affiliates",
                first_name=user_data.get("first_name", ""),
                last_name=user_data.get("last_name", ""),
                title=member.get("title", ""),
                university=member.get("university", ""),
                short_brief=user_data.get("short_brief", ""),
                image=doc,
                linkedin=user_data.get("linkedIn", ""),
                twitter=user_data.get("twitter", ""),
                facebook=user_data.get("facebook", ""),
                order=i,
                is_active=True,
            )

        total_members = len(exec_team) + len(affiliates)
        self.stdout.write(self.style.SUCCESS(f"Imported {total_members} team members"))

    def _import_testimonials(self, testimonials_data):
        """Import testimonials"""
        # Clear existing testimonials
        Testimonial.objects.all().delete()

        for testimonial in testimonials_data:
            user_data = testimonial.get("user", {})
            image_url = user_data.get("profile_img", "")
            doc = None
            if image_url:
                doc, _ = self._get_or_create_document(image_url)

            Testimonial.objects.create(
                first_name=user_data.get("firstName", ""),
                last_name=user_data.get("lastName", ""),
                role=user_data.get("role", ""),
                city=user_data.get("city", ""),
                profile_img=doc,
                rating=testimonial.get("ratting", 5),
                comment=testimonial.get("comment", ""),
                is_active=True,
            )

        self.stdout.write(self.style.SUCCESS(f"Imported {len(testimonials_data)} testimonials"))
