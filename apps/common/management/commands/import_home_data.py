import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.base import ContentFile
import requests
import tempfile
from urllib.parse import urlparse

from apps.common.models import (
    HomePage,
    HeroSectionImage,
    PartnerShip,
    WayToFileTax,
    Service,
    TeamMember,
    Testimonial
)
from apps.document.models import TainoDocument
from apps.document.services.document import DocumentService


class Command(BaseCommand):
    help = 'Import homepage data from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file to import')

    def handle(self, *args, **options):
        json_file_path = options['json_file']

        if not os.path.exists(json_file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {json_file_path}'))
            return

        try:
            with open(json_file_path, 'r') as file:
                data = json.load(file)

            if not data.get('status', False) or not data.get('data'):
                self.stdout.write(self.style.ERROR('Invalid JSON structure. Expected "status" and "data" fields.'))
                return

            home_data = data['data']
            self._import_home_data(home_data)

            self.stdout.write(self.style.SUCCESS('Successfully imported home data'))

        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('Invalid JSON file'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing data: {str(e)}'))

    def _import_home_data(self, home_data):
        # Create homepage
        homepage = HomePage.objects.create(
            header_title=home_data.get('header_title', ''),
            header_sub_title=home_data.get('header_Sub_title_', ''),  # Note the different case in JSON
            why=home_data.get('why', ''),
            why_point1=home_data.get('why_point1', ''),
            why_point2=home_data.get('why_point2', ''),
            why_point3=home_data.get('why_point3', ''),
            why_point4=home_data.get('why_point4', ''),
            how_to_file_tax_title=home_data.get('how_to_file_tax_title', ''),
            how_to_file_tax_short_description=home_data.get('how_to_file_tax_short_description', ''),
            is_active=True
        )

        # Process corporate strategy if exists
        corporate_strategy = home_data.get('corporate_strategy')
        if corporate_strategy:
            # Download and save corporate strategy image
            if 'img1' in corporate_strategy:
                corporate_img = self._download_and_create_document(corporate_strategy['img1'])
                if corporate_img:
                    homepage.corporate_strategy_img = corporate_img

            homepage.corporate_strategy_title = corporate_strategy.get('title', '')
            homepage.corporate_strategy_description = corporate_strategy.get('description', '')
            homepage.corporate_strategy_section1 = corporate_strategy.get('section1', '')
            homepage.corporate_strategy_section1_des = corporate_strategy.get('section1_des', '')
            homepage.corporate_strategy_section2 = corporate_strategy.get('section2', '')
            homepage.corporate_strategy_section2_des = corporate_strategy.get('section2_des', '')
            homepage.save()

        # Import hero section images
        self._import_hero_section_images(homepage, home_data.get('hero_section_images', []))

        # Import partnerships
        self._import_partnerships(homepage, home_data.get('partner_ships', []))

        # Import ways to file tax
        self._import_ways_to_file_tax(homepage, home_data.get('way_to_file_tax', []))

        # Import services
        self._import_services(homepage, home_data.get('services', []))

        # Import testimonials
        self._import_testimonials(home_data.get('testimonials', []))

        # Import team members
        self._import_team_members(home_data.get('team_members', {}))

        self.stdout.write(self.style.SUCCESS(f'Created homepage: {homepage.header_title}'))

    def _import_hero_section_images(self, homepage, image_urls):
        for i, image_url in enumerate(image_urls):
            document = self._download_and_create_document(image_url)
            if document:
                HeroSectionImage.objects.create(
                    home_page=homepage,
                    image=document,
                    order=i
                )
                self.stdout.write(self.style.SUCCESS(f'Created hero section image {i+1}'))

    def _import_partnerships(self, homepage, image_urls):
        for i, image_url in enumerate(image_urls):
            document = self._download_and_create_document(image_url)
            if document:
                PartnerShip.objects.create(
                    home_page=homepage,
                    image=document,
                    order=i
                )
                self.stdout.write(self.style.SUCCESS(f'Created partnership {i+1}'))

    def _import_ways_to_file_tax(self, homepage, ways_data):
        for i, way_data in enumerate(ways_data):
            document = self._download_and_create_document(way_data.get('image', ''))
            if document:
                WayToFileTax.objects.create(
                    home_page=homepage,
                    title=way_data.get('title', ''),
                    description=way_data.get('description', ''),
                    image=document,
                    order=i,
                    is_active=True
                )
                self.stdout.write(self.style.SUCCESS(f'Created way to file tax: {way_data.get("title", "")}'))

    def _import_services(self, homepage, services_data):
        for i, service_data in enumerate(services_data):
            document = self._download_and_create_document(service_data.get('logo', ''))
            if document:
                Service.objects.create(
                    home_page=homepage,
                    title=service_data.get('title', ''),
                    description=service_data.get('description', ''),
                    logo=document,
                    order=i,
                    is_active=True
                )
                self.stdout.write(self.style.SUCCESS(f'Created service: {service_data.get("title", "")}'))

    def _import_testimonials(self, testimonials_data):
        for i, testimonial_data in enumerate(testimonials_data):
            user_data = testimonial_data.get('user', {})
            profile_img = self._download_and_create_document(user_data.get('profile_img', ''))

            Testimonial.objects.create(
                first_name=user_data.get('firstName', ''),
                last_name=user_data.get('lastName', ''),
                role=user_data.get('role', ''),
                city=user_data.get('city', ''),
                profile_img=profile_img,
                rating=testimonial_data.get('ratting', 5),  # Note the typo in JSON
                comment=testimonial_data.get('comment', ''),
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'Created testimonial for {user_data.get("firstName", "")} {user_data.get("lastName", "")}'))

    def _import_team_members(self, team_data):
        # Import executive team
        exec_team = team_data.get('executive_team', [])
        for i, member_data in enumerate(exec_team):
            user_data = member_data.get('user', {})
            image = self._download_and_create_document(user_data.get('image', ''))

            TeamMember.objects.create(
                team_type='executive_team',
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                title=member_data.get('title', ''),
                university=member_data.get('university', ''),
                short_brief=user_data.get('short_brief', ''),
                image=image,
                linkedin=user_data.get('linkedIn', ''),
                twitter=user_data.get('twitter', ''),
                facebook=user_data.get('facebook', ''),
                order=i,
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'Created executive team member: {user_data.get("first_name", "")} {user_data.get("last_name", "")}'))

        # Import accounting affiliates
        affiliates = team_data.get('accounting_affiliates', [])
        for i, member_data in enumerate(affiliates):
            user_data = member_data.get('user', {})
            image = self._download_and_create_document(user_data.get('image', ''))

            TeamMember.objects.create(
                team_type='accounting_affiliates',
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                title=member_data.get('title', ''),
                university=member_data.get('university', ''),
                short_brief=user_data.get('short_brief', ''),
                image=image,
                order=i,
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'Created accounting affiliate: {user_data.get("first_name", "")} {user_data.get("last_name", "")}'))

    def _download_and_create_document(self, url):
        """Download an image from URL and create a document"""
        if not url:
            return None

        try:
            # Parse URL to get filename
            parsed_url = urlparse(url)
            path = parsed_url.path
            filename = os.path.basename(path)

            # Download the file
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                self.stdout.write(self.style.WARNING(f'Failed to download file from {url}'))
                return None

            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        temp_file.write(chunk)
                temp_file_path = temp_file.name

            # Get content type from Django
            from django.contrib.contenttypes.models import ContentType
            document_content_type = ContentType.objects.get_for_model(HomePage)

            # Create document
            with open(temp_file_path, 'rb') as f:
                document = TainoDocument.objects.create(
                    file=ContentFile(f.read(), name=filename),
                    content_type=document_content_type,
                    document_type='image',
                    is_public=True
                )

            # Clean up temporary file
            os.unlink(temp_file_path)

            return document

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error downloading file {url}: {str(e)}'))
            return None