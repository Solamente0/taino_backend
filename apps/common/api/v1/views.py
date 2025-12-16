import logging

from django.db import IntegrityError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.api.v1.filters import (
    FrequentlyAskedQuestionFilter,
    TermsOfUseFilter,
    ServiceItemFilter,
    TutorialVideoFilter,
    ServiceCategoryFilter,
)
from apps.common.api.v1.serializers.about_us import AboutUsTeamMemberSerializer
from apps.common.api.v1.serializers.tutorial_video import TutorialVideoSerializer

from apps.common.models import (
    HomePage,
    FrequentlyAskedQuestion,
    TermsOfUse,
    Newsletter,
    ServiceItem,
    TutorialVideo,
    ServiceCategory,
)
from apps.common.api.v1.serializers import (
    HomePageSerializer,
    FrequentlyAskedQuestionSerializer,
    TermsOfUseSerializer,
    NewsletterUnsubscribeSerializer,
    NewsletterSubscribeSerializer,
    ContactUsSerializer,
    ServiceItemSerializer,
    AboutUsSerializer,
    ServiceCategorySerializer,
)
from apps.common.models import AboutUs, AboutUsTeamMember
from base_utils.filters import IsActiveFilterBackend
from base_utils.views.mobile import TainoMobileReadOnlyModelViewSet, TainoMobileAPIView

log = logging.getLogger(__name__)


class HomePageView(APIView):
    # permission_classes = [AllowAny]
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        try:
            # Get the most recent active home page
            homepage = HomePage.objects.filter(is_active=True).latest("created_at")
            serializer = HomePageSerializer(homepage)
            return Response({"status": True, "data": serializer.data})
        except HomePage.DoesNotExist:
            return Response({"status": False, "message": "No active home page found"})
        except Exception as e:
            log.error(f"Error fetching home page: {str(e)}")
            return Response({"status": False, "message": "Error fetching home page data"})


class FrequentlyAskedQuestionViewSet(TainoMobileReadOnlyModelViewSet):
    queryset = FrequentlyAskedQuestion.objects.filter(is_active=True)
    serializer_class = FrequentlyAskedQuestionSerializer
    permission_classes = [AllowAny]

    filter_backends = [IsActiveFilterBackend, SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["question", "answer"]
    ordering_fields = ["order", "created_at", "updated_at"]
    filterset_class = FrequentlyAskedQuestionFilter
    ordering = ["order"]


class TermsOfUseViewSet(TainoMobileReadOnlyModelViewSet):
    queryset = TermsOfUse.objects.filter(is_active=True)
    serializer_class = TermsOfUseSerializer
    permission_classes = [AllowAny]

    filter_backends = [IsActiveFilterBackend, SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["title", "content"]
    ordering_fields = ["order", "created_at", "updated_at"]
    filterset_class = TermsOfUseFilter
    ordering = ["order"]


class ContactUsAPIView(TainoMobileAPIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ContactUsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"status": True, "message": "Your message has been sent successfully"}, status=status.HTTP_201_CREATED
        )


class NewsletterSubscribeAPIView(TainoMobileAPIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = NewsletterSubscribeSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save(is_active=True)
                return Response(
                    {"status": True, "message": "You have been subscribed to our newsletter"}, status=status.HTTP_201_CREATED
                )
            except IntegrityError:
                # Handle case where email already exists but might be inactive
                newsletter = Newsletter.objects.get(email=serializer.validated_data["email"])
                if not newsletter.is_active:
                    newsletter.is_active = True
                    newsletter.save()
                    return Response(
                        {"status": True, "message": "Your subscription has been reactivated"}, status=status.HTTP_200_OK
                    )
                return Response(
                    {"status": True, "message": "You are already subscribed to our newsletter"}, status=status.HTTP_200_OK
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NewsletterUnsubscribeAPIView(TainoMobileAPIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = NewsletterUnsubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            newsletter = Newsletter.objects.get(unsubscribe_token=serializer.validated_data["token"])
            newsletter.is_active = False
            newsletter.save()
            return Response(
                {"status": True, "message": "You have been unsubscribed from our newsletter"}, status=status.HTTP_200_OK
            )
        except Newsletter.DoesNotExist:
            return Response({"status": False, "message": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


class ServiceItemViewSet(TainoMobileReadOnlyModelViewSet):
    serializer_class = ServiceItemSerializer
    permission_classes = [AllowAny]

    filter_backends = [IsActiveFilterBackend, SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["name", "description", "static_name"]
    ordering_fields = ["order", "created_at", "updated_at"]
    filterset_class = ServiceItemFilter
    ordering = ["order"]

    def get_queryset(self):
        """
        Filter services based on user role and optimize with select_related/prefetch_related

        Logic:
        - If service has NO roles assigned: show to everyone
        - If service has roles assigned: only show to users with matching role
        """
        from django.db.models import Q, Count

        queryset = (
            ServiceItem.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("roles")
            .annotate(role_count=Count("roles"))
        )

        # Filter by user role
        if self.request.user and self.request.user.is_authenticated and self.request.user.role:
            # Show services with no roles OR services with user's role
            queryset = queryset.filter(Q(role_count=0) | Q(roles=self.request.user.role))
        else:
            # For anonymous users, only show services with no role restrictions
            queryset = queryset.filter(role_count=0)

        # Filter by category if provided in query params
        category_static_name = self.request.query_params.get("category", None)
        if category_static_name:
            queryset = queryset.filter(category__static_name=category_static_name, category__is_active=True)

        return queryset.distinct()

    @action(detail=False, methods=["get"], url_path="check/(?P<static_name>[^/.]+)")
    def check_service(self, request, static_name=None):
        """
        Check if a service with the given static_name exists, is active, and accessible to user's role
        """
        from django.db.models import Q, Count

        queryset = (
            ServiceItem.objects.filter(static_name=static_name, is_active=True)
            .prefetch_related("roles")
            .annotate(role_count=Count("roles"))
        )

        # Filter by authenticated user's role
        if request.user and request.user.is_authenticated and request.user.role:
            queryset = queryset.filter(Q(role_count=0) | Q(roles=request.user.role))
        else:
            queryset = queryset.filter(role_count=0)

        service = queryset.first()

        if service:
            return Response({"status": True, "data": ServiceItemSerializer(service).data}, status=status.HTTP_200_OK)
        return Response(
            {"status": False, "message": f"Service with static name '{static_name}' is not available"},
            status=status.HTTP_404_NOT_FOUND,
        )

    @action(detail=False, methods=["get"], url_path="by-category/(?P<category_static_name>[^/.]+)")
    def by_category(self, request, category_static_name=None):
        """
        Get all services in a specific category filtered by user role
        Example: /api/v1/common/service-items/by-category/legal-services/
        """
        from django.db.models import Q, Count

        try:
            # First check if category exists and is active
            category = (
                ServiceCategory.objects.filter(static_name=category_static_name, is_active=True)
                .prefetch_related("roles")
                .annotate(role_count=Count("roles"))
                .first()
            )

            if not category:
                return Response(
                    {"status": False, "message": f"Category '{category_static_name}' not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Check if user has access to this category
            if request.user and request.user.is_authenticated and request.user.role:
                # Category with no roles OR user has the role
                if category.role_count > 0 and not category.roles.filter(id=request.user.role.id).exists():
                    return Response(
                        {"status": False, "message": "You don't have access to this category"},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            else:
                # Anonymous users can only access categories with no roles
                if category.role_count > 0:
                    return Response(
                        {"status": False, "message": "This category requires authentication"},
                        status=status.HTTP_403_FORBIDDEN,
                    )

            # Get services filtered by user's role
            services = (
                ServiceItem.objects.filter(category=category, is_active=True)
                .select_related("category")
                .prefetch_related("roles")
                .annotate(role_count=Count("roles"))
            )

            if request.user and request.user.is_authenticated and request.user.role:
                services = services.filter(Q(role_count=0) | Q(roles=request.user.role))
            else:
                services = services.filter(role_count=0)

            services = services.order_by("order").distinct()

            serializer = ServiceItemSerializer(services, many=True)
            return Response({"status": True, "data": serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            log.error(f"Error fetching services by category: {str(e)}")
            return Response(
                {"status": False, "message": "Error fetching services"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"], url_path="active")
    def active_services(self, request):
        """
        Get all active services filtered by user role, optionally grouped by category
        """
        from django.db.models import Q, Count

        group_by_category = request.query_params.get("group_by_category", "false").lower() == "true"

        # Build optimized queryset
        services = (
            ServiceItem.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("roles", "category__roles")
            .annotate(role_count=Count("roles"))
        )

        # Filter by authenticated user's role
        if request.user and request.user.is_authenticated and request.user.role:
            services = services.filter(Q(role_count=0) | Q(roles=request.user.role))
        else:
            services = services.filter(role_count=0)

        services = services.order_by("order").distinct()

        if group_by_category:
            # Group services by category
            result = {}
            for service in services:
                # Skip services with inaccessible categories
                if service.category:
                    category_role_count = service.category.roles.count()

                    # Check category role access
                    if request.user and request.user.is_authenticated and request.user.role:
                        if category_role_count > 0 and not service.category.roles.filter(id=request.user.role.id).exists():
                            continue
                    else:
                        if category_role_count > 0:
                            continue

                    category_name = service.category.name
                    category_static_name = service.category.static_name
                else:
                    category_name = "uncategorized"
                    category_static_name = "uncategorized"

                if category_static_name not in result:
                    result[category_static_name] = {
                        "category_name": category_name,
                        "category_static_name": category_static_name,
                        "services": [],
                    }

                result[category_static_name]["services"].append(ServiceItemSerializer(service).data)

            return Response({"status": True, "data": result}, status=status.HTTP_200_OK)

        # Default: Return flat list
        serializer = ServiceItemSerializer(services, many=True)
        return Response({"status": True, "data": serializer.data}, status=status.HTTP_200_OK)


class ServiceCategoryViewSet(TainoMobileReadOnlyModelViewSet):
    """
    API endpoint for retrieving service categories with hierarchical support

    Endpoints:
    - GET /api/v1/common/service-categories/ - List all root categories (backward compatible)
    - GET /api/v1/common/service-categories/?include_children=true - List with children
    - GET /api/v1/common/service-categories/{pid}/ - Get specific category
    - GET /api/v1/common/service-categories/by-static-name/{static_name}/ - Get by static_name with children
    - GET /api/v1/common/service-categories/with-services/ - Get categories with their services
    - GET /api/v1/common/service-categories/tree/ - Get full category tree
    """

    serializer_class = ServiceCategorySerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [IsActiveFilterBackend, SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["name", "description", "static_name"]
    ordering_fields = ["order", "created_at", "updated_at"]
    filterset_class = ServiceCategoryFilter
    ordering = ["order"]

    def get_queryset(self):
        """
        Filter categories based on user role
        By default, only return root categories (parent=None) for backward compatibility
        """
        from django.db.models import Q, Count

        queryset = (
            ServiceCategory.objects.filter(is_active=True)
            .select_related("parent")
            .prefetch_related("roles", "children")
            .annotate(role_count=Count("roles"))
        )

        # Filter by authenticated user's role
        if self.request.user and self.request.user.is_authenticated and self.request.user.role:
            queryset = queryset.filter(Q(role_count=0) | Q(roles=self.request.user.role))
        else:
            queryset = queryset.filter(role_count=0)

        # Backward compatibility: only return root categories by default
        # Unless explicitly requesting all levels
        if self.action == "list" and not self.request.query_params.get("all_levels"):
            queryset = queryset.filter(parent=None)

        return queryset.distinct()

    def get_serializer_context(self):
        """Add context flags for controlling serializer behavior"""
        context = super().get_serializer_context()

        # Include children if requested
        include_children = self.request.query_params.get("include_children", "false").lower() == "true"
        context["include_children"] = include_children

        # Include ancestors if requested
        include_ancestors = self.request.query_params.get("include_ancestors", "false").lower() == "true"
        context["include_ancestors"] = include_ancestors

        return context

    @action(detail=False, methods=["get"], url_path="by-static-name/(?P<static_name>[^/.]+)")
    def by_static_name(self, request, static_name=None):
        """
        Get a category by its static_name with all its children categories
        Example: /api/v1/common/service-categories/by-static-name/legal-services/

        Returns the category with all descendant categories (children, grandchildren, etc.)
        """
        from django.db.models import Q, Count

        queryset = (
            ServiceCategory.objects.filter(static_name=static_name, is_active=True)
            .select_related("parent")
            .prefetch_related("roles", "children")
            .annotate(role_count=Count("roles"))
        )

        # Filter by authenticated user's role
        if request.user and request.user.is_authenticated and request.user.role:
            queryset = queryset.filter(Q(role_count=0) | Q(roles=request.user.role))
        else:
            queryset = queryset.filter(role_count=0)

        category = queryset.first()

        if not category:
            return Response(
                {"status": False, "message": f"Category with static name '{static_name}' not found or not accessible"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Always include children for this endpoint
        context = self.get_serializer_context()
        context["include_children"] = True
        context["include_ancestors"] = True

        serializer = ServiceCategorySerializer(category, context=context)

        return Response({"status": True, "data": serializer.data}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="with-services")
    def with_services(self, request):
        """
        Get all categories with their associated services
        When a category is requested, it returns services from that category AND all its children

        Query params:
        - category_static_name: Filter by specific category (includes children's services)
        - include_children: Include child categories in response
        """
        from django.db.models import Q, Count

        category_static_name = request.query_params.get("category_static_name")

        # Get categories filtered by user's role
        categories = (
            ServiceCategory.objects.filter(is_active=True)
            .select_related("parent")
            .prefetch_related("roles", "children", "service_items__roles")
            .annotate(role_count=Count("roles"))
        )

        if request.user and request.user.is_authenticated and request.user.role:
            categories = categories.filter(Q(role_count=0) | Q(roles=request.user.role))
        else:
            categories = categories.filter(role_count=0)

        # Filter by specific category if requested
        if category_static_name:
            parent_category = categories.filter(static_name=category_static_name).first()
            if not parent_category:
                return Response(
                    {"status": False, "message": f"Category '{category_static_name}' not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Get all children categories (recursive)
            all_category_ids = [parent_category.id]
            all_category_ids.extend([child.id for child in parent_category.get_all_children()])

            categories = categories.filter(id__in=all_category_ids)
        else:
            # Default: only root categories for backward compatibility
            categories = categories.filter(parent=None)

        categories = categories.order_by("order").distinct()

        result = []
        for category in categories:
            context = self.get_serializer_context()
            category_data = ServiceCategorySerializer(category, context=context).data

            # Get services for this category AND all its children
            category_ids = [category.id]
            category_ids.extend([child.id for child in category.get_all_children()])

            services = (
                ServiceItem.objects.filter(category_id__in=category_ids, is_active=True)
                .select_related("category")
                .prefetch_related("roles")
                .annotate(service_role_count=Count("roles"))
            )

            if request.user and request.user.is_authenticated and request.user.role:
                services = services.filter(Q(service_role_count=0) | Q(roles=request.user.role))
            else:
                services = services.filter(service_role_count=0)

            services = services.order_by("order").distinct()

            category_data["services"] = ServiceItemSerializer(services, many=True).data
            category_data["total_services"] = services.count()

            result.append(category_data)

        return Response({"status": True, "data": result}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="tree")
    def category_tree(self, request):
        """
        Get the full category tree structure
        Example: /api/v1/common/service-categories/tree/

        Returns hierarchical tree of all categories
        """
        from django.db.models import Q, Count

        # Get only root categories
        root_categories = (
            ServiceCategory.objects.filter(is_active=True, parent=None)
            .prefetch_related("roles", "children")
            .annotate(role_count=Count("roles"))
        )

        if request.user and request.user.is_authenticated and request.user.role:
            root_categories = root_categories.filter(Q(role_count=0) | Q(roles=request.user.role))
        else:
            root_categories = root_categories.filter(role_count=0)

        root_categories = root_categories.order_by("order").distinct()

        # Force include children for tree view
        context = self.get_serializer_context()
        context["include_children"] = True

        serializer = ServiceCategorySerializer(root_categories, many=True, context=context)

        return Response({"status": True, "data": serializer.data}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="roots")
    def root_categories(self, request):
        """
        Explicitly get only root categories (parent=None)
        Example: /api/v1/common/service-categories/roots/
        """
        from django.db.models import Q, Count

        root_categories = (
            ServiceCategory.objects.filter(is_active=True, parent=None)
            .prefetch_related("roles")
            .annotate(role_count=Count("roles"))
        )

        if request.user and request.user.is_authenticated and request.user.role:
            root_categories = root_categories.filter(Q(role_count=0) | Q(roles=request.user.role))
        else:
            root_categories = root_categories.filter(role_count=0)

        root_categories = root_categories.order_by("order").distinct()

        serializer = ServiceCategorySerializer(root_categories, many=True)

        return Response({"status": True, "data": serializer.data}, status=status.HTTP_200_OK)


class AboutUsAPIView(APIView):
    """
    API endpoint for retrieving About Us information and team members
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        try:
            # Get the most recent active about us page
            about_us = AboutUs.objects.filter(is_active=True).latest("created_at")
            serializer = AboutUsSerializer(about_us)
            return Response({"status": True, "data": serializer.data})
        except AboutUs.DoesNotExist:
            return Response({"status": False, "message": "No active about us page found"})
        except Exception as e:
            log.error(f"Error fetching about us page: {str(e)}")
            return Response({"status": False, "message": "Error fetching about us data"})


class AboutUsTeamMemberViewSet(TainoMobileReadOnlyModelViewSet):
    """
    API endpoint for listing and retrieving team members
    """

    queryset = AboutUsTeamMember.objects.filter(is_active=True)
    serializer_class = AboutUsTeamMemberSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset().order_by("order")
        about_us_pid = self.request.query_params.get("about_us", None)

        if about_us_pid:
            queryset = queryset.filter(about_us__pid=about_us_pid)

        return queryset


@method_decorator(ensure_csrf_cookie, name="dispatch")
class EnsureCookieAPIView(TainoMobileAPIView):
    """
    Ensures that the CSRF cookie is set for the client.
    This endpoint can be called by the Next.js app to establish CSRF protection.
    """

    permission_classes = [AllowAny]
    authentication_classes = []  # No authentication required

    def get(self, request, *args, **kwargs):
        return Response({"status": True, "message": "CSRF cookie set"})


class TutorialVideoViewSet(TainoMobileReadOnlyModelViewSet):
    """
    API endpoint for retrieving tutorial videos for frontend routes

    Endpoints:
    - GET /api/v1/common/tutorial-videos/ - List all active tutorial videos
    - GET /api/v1/common/tutorial-videos/{pid}/ - Get specific tutorial video
    - GET /api/v1/common/tutorial-videos/by-route/?route_path=/dashboard - Get tutorial for specific route
    """

    queryset = TutorialVideo.objects.filter(is_active=True)
    serializer_class = TutorialVideoSerializer
    permission_classes = [AllowAny]

    filter_backends = [IsActiveFilterBackend, SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["title", "name", "description", "route_path", "tags"]
    ordering_fields = ["order", "created_at", "updated_at"]
    filterset_class = TutorialVideoFilter
    ordering = ["order"]

    @action(detail=False, methods=["get"], url_path="by-route")
    def get_by_route(self, request):
        """
        Get tutorial video for a specific route
        Query params: route_path (required)

        Example: /api/v1/common/tutorial-videos/by-route/?route_path=/dashboard
        """
        route_path = request.query_params.get("route_path")

        if not route_path:
            return Response(
                {"status": False, "message": "route_path parameter is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        tutorial = TutorialVideo.objects.filter(route_path=route_path, is_active=True).first()

        if tutorial:
            serializer = TutorialVideoSerializer(tutorial)
            return Response({"status": True, "data": serializer.data}, status=status.HTTP_200_OK)

        return Response(
            {"status": False, "message": f"No tutorial found for route: {route_path}"}, status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=False, methods=["get"], url_path="first-visit")
    def first_visit_tutorials(self, request):
        """
        Get all tutorials that should be shown on first visit

        Example: /api/v1/common/tutorial-videos/first-visit/
        """
        tutorials = TutorialVideo.objects.filter(is_active=True, show_on_first_visit=True).order_by("order")

        serializer = TutorialVideoSerializer(tutorials, many=True)
        return Response({"status": True, "data": serializer.data}, status=status.HTTP_200_OK)
