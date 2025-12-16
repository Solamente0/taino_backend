from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from apps.common.models import (
    HomePage,
    HeroSectionImage,
    PartnerShip,
    WayToFileTax,
    Service,
    TeamMember,
    Testimonial
)
from base_utils.base_tests import TainoBaseAPITestCase


class HomePageAPITest(TainoBaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("common:common_v1:home")

        # Create test data
        self.homepage = baker.make(
            HomePage,
            header_title="Test Header Title",
            header_sub_title="Test Header Subtitle",
            why="Test Why Section",
            why_point1="Test Point 1",
            why_point2="Test Point 2",
            why_point3="Test Point 3",
            why_point4="Test Point 4",
            how_to_file_tax_title="Test Filing Tax Title",
            how_to_file_tax_short_description="Test Filing Tax Description",
            is_active=True,
        )

        # Create related data
        self.hero_images = baker.make(HeroSectionImage, home_page=self.homepage, _quantity=2)
        self.partnerships = baker.make(PartnerShip, home_page=self.homepage, _quantity=3)
        self.ways_to_file_tax = baker.make(
            WayToFileTax,
            home_page=self.homepage,
            title="Test Way to File Tax",
            description="Test Description",
            is_active=True,
            _quantity=2
        )
        self.services = baker.make(
            Service,
            home_page=self.homepage,
            title="Test Service",
            description="Test Service Description",
            is_active=True,
            _quantity=2
        )
        self.executive_team = baker.make(
            TeamMember,
            team_type="executive_team",
            first_name="Test Exec",
            last_name="Member",
            title="Test Executive Title",
            is_active=True,
            _quantity=2
        )
        self.accounting_affiliates = baker.make(
            TeamMember,
            team_type="accounting_affiliates",
            first_name="Test Accounting",
            last_name="Affiliate",
            title="Test Accounting Title",
            is_active=True,
            _quantity=2
        )
        self.testimonials = baker.make(
            Testimonial,
            first_name="Test",
            last_name="User",
            role="small_business",
            city="New York",
            rating=5,
            comment="Test Comment",
            is_active=True,
            _quantity=3
        )

    def test_homepage_api(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])

        data = response.data['data']
        self.assertEqual(data['header_title'], self.homepage.header_title)
        self.assertEqual(data['header_sub_title'], self.homepage.header_sub_title)
        self.assertEqual(data['why'], self.homepage.why)
        self.assertEqual(data['why_point1'], self.homepage.why_point1)
        self.assertEqual(len(data['way_to_file_tax']), 2)
        self.assertEqual(len(data['services']), 2)

    def test_homepage_api_without_login(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])

        data = response.data['data']
        self.assertEqual(data['header_title'], self.homepage.header_title)