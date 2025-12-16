from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response

from apps.common.api.admin.filters import (
    HomePageAdminFilter,
    HeroSectionImageAdminFilter,
    PartnerShipAdminFilter,
    WayToFileTaxAdminFilter,
    ServiceAdminFilter,
    TeamMemberAdminFilter,
    TestimonialAdminFilter,
    FrequentlyAskedQuestionAdminFilter,
    TermsOfUseAdminFilter,
    NewsletterAdminFilter,
    ContactUsAdminFilter,
    ServiceItemAdminFilter,
    AboutUsTeamMemberAdminFilter,
    AboutUsAdminFilter,
    TutorialVideoAdminFilter,
    ServiceCategoryAdminFilter,
)
from .serializers import (
    HomePageAdminSerializer,
    HeroSectionImageAdminSerializer,
    PartnerShipAdminSerializer,
    WayToFileTaxAdminSerializer,
    ServiceAdminSerializer,
    TeamMemberAdminSerializer,
    TestimonialAdminSerializer,
    FrequentlyAskedQuestionAdminSerializer,
    TermsOfUseAdminSerializer,
    ContactUsAdminSerializer,
    ServiceItemAdminSerializer,
    ServiceCategoryAdminSerializer,
)
from apps.common.api.admin.serializers.subscribe import NewsletterAdminSerializer
from apps.common.models import (
    HomePage,
    HeroSectionImage,
    PartnerShip,
    WayToFileTax,
    Service,
    TeamMember,
    Testimonial,
    FrequentlyAskedQuestion,
    TermsOfUse,
    Newsletter,
    ContactUs,
    ServiceItem,
    AboutUs,
    AboutUsTeamMember,
    TutorialVideo,
    ServiceCategory,
)
from base_utils.views.admin import TainoAdminModelViewSet
from .serializers.about_us import AboutUsAdminSerializer, AboutUsTeamMemberAdminSerializer
from .serializers.tutorial_video import TutorialVideoAdminSerializer


class HomePageAdminViewSet(TainoAdminModelViewSet):
    queryset = HomePage.objects.all()
    serializer_class = HomePageAdminSerializer

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["header_title", "header_sub_title"]
    ordering_fields = ["created_at", "updated_at"]
    filterset_class = HomePageAdminFilter
    ordering = ["-created_at"]


class HeroSectionImageAdminViewSet(TainoAdminModelViewSet):
    queryset = HeroSectionImage.objects.all()
    serializer_class = HeroSectionImageAdminSerializer

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["order", "created_at"]
    filterset_class = HeroSectionImageAdminFilter
    ordering = ["order"]


class PartnerShipAdminViewSet(TainoAdminModelViewSet):
    queryset = PartnerShip.objects.all()
    serializer_class = PartnerShipAdminSerializer

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["order", "created_at"]
    filterset_class = PartnerShipAdminFilter
    ordering = ["order"]


class WayToFileTaxAdminViewSet(TainoAdminModelViewSet):
    queryset = WayToFileTax.objects.all()
    serializer_class = WayToFileTaxAdminSerializer

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["order", "created_at", "updated_at"]
    filterset_class = WayToFileTaxAdminFilter
    ordering = ["order"]


class ServiceAdminViewSet(TainoAdminModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceAdminSerializer

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["order", "created_at", "updated_at"]
    filterset_class = ServiceAdminFilter
    ordering = ["order"]


class TeamMemberAdminViewSet(TainoAdminModelViewSet):
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberAdminSerializer

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["first_name", "last_name", "title", "university"]
    ordering_fields = ["team_type", "order", "created_at", "updated_at"]
    filterset_class = TeamMemberAdminFilter
    ordering = ["team_type", "order"]


class TestimonialAdminViewSet(TainoAdminModelViewSet):
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialAdminSerializer

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["first_name", "last_name", "role", "city", "comment"]
    ordering_fields = ["rating", "created_at", "updated_at"]
    filterset_class = TestimonialAdminFilter
    ordering = ["-created_at"]


class FrequentlyAskedQuestionAdminViewSet(TainoAdminModelViewSet):
    queryset = FrequentlyAskedQuestion.objects.all()
    serializer_class = FrequentlyAskedQuestionAdminSerializer

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["question", "answer"]
    ordering_fields = ["order", "created_at", "updated_at"]
    filterset_class = FrequentlyAskedQuestionAdminFilter
    ordering = ["order"]


class TermsOfUseAdminViewSet(TainoAdminModelViewSet):
    queryset = TermsOfUse.objects.all()
    serializer_class = TermsOfUseAdminSerializer

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["title", "content"]
    ordering_fields = ["order", "created_at", "updated_at"]
    filterset_class = TermsOfUseAdminFilter
    ordering = ["order"]


class ContactUsAdminViewSet(TainoAdminModelViewSet):
    queryset = ContactUs.objects.all()
    serializer_class = ContactUsAdminSerializer

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["name", "email", "subject", "message"]
    ordering_fields = ["created_at", "is_read"]
    filterset_class = ContactUsAdminFilter
    ordering = ["-created_at"]


class NewsletterAdminViewSet(TainoAdminModelViewSet):
    queryset = Newsletter.objects.all()
    serializer_class = NewsletterAdminSerializer

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["email"]
    ordering_fields = ["created_at", "is_active"]
    filterset_class = NewsletterAdminFilter
    ordering = ["-created_at"]


class ServiceItemAdminViewSet(TainoAdminModelViewSet):
    queryset = ServiceItem.objects.all()
    serializer_class = ServiceItemAdminSerializer

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["static_name", "name", "description"]
    ordering_fields = ["order", "created_at", "updated_at"]
    filterset_class = ServiceItemAdminFilter
    ordering = ["order"]

    def get_queryset(self):
        queryset = super().get_queryset()
        category_pid = self.request.query_params.get("category", None)

        if category_pid:
            queryset = queryset.filter(category__pid=category_pid)

        return queryset

    @action(detail=False, methods=["get"], url_path="check/(?P<static_name>[^/.]+)")
    def check_service(self, request, static_name=None):
        """
        Check if a service with the given static_name exists and is active
        """
        service = ServiceItem.objects.filter(static_name=static_name, is_active=True).first()
        if service:
            return Response({"status": True, "data": ServiceItemAdminSerializer(service).data}, status=status.HTTP_200_OK)
        return Response(
            {"status": False, "message": f"Service with static name '{static_name}' is not available"},
            status=status.HTTP_404_NOT_FOUND,
        )

    @action(detail=False, methods=["get"], url_path="by-category/(?P<category_static_name>[^/.]+)")
    def by_category(self, request, category_static_name=None):
        """
        Get all services in a specific category by category static_name
        """
        try:
            category = ServiceCategory.objects.get(static_name=category_static_name, is_active=True)
            services = ServiceItem.objects.filter(category=category, is_active=True).order_by("order")
            serializer = ServiceItemAdminSerializer(services, many=True)
            return Response({"status": True, "data": serializer.data}, status=status.HTTP_200_OK)
        except ServiceCategory.DoesNotExist:
            return Response(
                {"status": False, "message": f"Category with static name '{category_static_name}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class AboutUsAdminViewSet(TainoAdminModelViewSet):
    queryset = AboutUs.objects.all()
    serializer_class = AboutUsAdminSerializer

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["title"]
    ordering_fields = ["created_at", "updated_at"]
    filterset_class = AboutUsAdminFilter
    ordering = ["-created_at"]


class AboutUsTeamMemberAdminViewSet(TainoAdminModelViewSet):
    queryset = AboutUsTeamMember.objects.all()
    serializer_class = AboutUsTeamMemberAdminSerializer

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["full_name", "job_title"]
    ordering_fields = ["order", "created_at", "updated_at"]
    filterset_class = AboutUsTeamMemberAdminFilter
    ordering = ["order"]


class TutorialVideoAdminViewSet(TainoAdminModelViewSet):
    """
    Admin API endpoint for managing tutorial videos
    """

    queryset = TutorialVideo.objects.all()
    serializer_class = TutorialVideoAdminSerializer

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["title", "name", "description", "route_path", "tags"]
    ordering_fields = ["order", "created_at", "updated_at"]
    filterset_class = TutorialVideoAdminFilter
    ordering = ["order"]


class ServiceCategoryAdminViewSet(TainoAdminModelViewSet):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategoryAdminSerializer

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["static_name", "name", "description"]
    ordering_fields = ["order", "created_at", "updated_at"]
    filterset_class = ServiceCategoryAdminFilter
    ordering = ["order"]

    @action(detail=False, methods=["get"], url_path="with-services")
    def with_services(self, request):
        """
        Get all categories with their associated services
        """
        categories = ServiceCategory.objects.filter(is_active=True).prefetch_related("service_items").order_by("order")

        result = []
        for category in categories:
            category_data = ServiceCategoryAdminSerializer(category).data
            category_data["services"] = ServiceItemAdminSerializer(
                category.service_items.filter(is_active=True).order_by("order"), many=True
            ).data
            result.append(category_data)

        return Response({"status": True, "data": result}, status=status.HTTP_200_OK)
