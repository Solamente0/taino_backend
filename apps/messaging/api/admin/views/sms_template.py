from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.messaging.api.admin.serializers import (
    AdminSMSTemplateSerializer,
    AdminSystemTemplateTestSerializer,
    AdminSystemSMSTemplateSerializer,
)
from apps.messaging.models import SMSTemplate, SystemSMSTemplate
from base_utils.views.admin import TainoAdminGenericViewSet

User = get_user_model()


class AdminSMSTemplateViewSet(TainoAdminGenericViewSet):
    """
    Admin ViewSet for managing SMS templates
    """

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "content", "creator__first_name", "creator__last_name"]
    filterset_fields = ["template_type", "is_system", "is_active"]
    ordering_fields = ["name", "created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Get all SMS templates"""
        return SMSTemplate.objects.all().select_related("creator")

    def get_serializer_class(self):
        """Select appropriate serializer based on action"""
        return AdminSMSTemplateSerializer

    @extend_schema(summary="List SMS templates", description="Admin endpoint to list all SMS templates")
    def list(self, request):
        """List all SMS templates"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(summary="Get SMS template details", description="Admin endpoint to get details of a specific SMS template")
    def retrieve(self, request, pk=None):
        """Get details of a specific SMS template"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(summary="Create SMS template", description="Admin endpoint to create a new SMS template")
    def create(self, request):
        """Create a new SMS template"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Set creator to current admin if not provided
        if "creator" not in serializer.validated_data:
            serializer.validated_data["creator"] = request.user

        template = serializer.save()

        return Response(self.get_serializer(template).data, status=status.HTTP_201_CREATED)

    @extend_schema(summary="Update SMS template", description="Admin endpoint to update an SMS template")
    def update(self, request, pk=None):
        """Update an SMS template"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        template = serializer.save()

        return Response(self.get_serializer(template).data)

    @extend_schema(summary="Partially update SMS template", description="Admin endpoint to partially update an SMS template")
    def partial_update(self, request, pk=None):
        """Partially update an SMS template"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        template = serializer.save()

        return Response(self.get_serializer(template).data)

    @extend_schema(summary="Delete SMS template", description="Admin endpoint to delete (deactivate) an SMS template")
    def destroy(self, request, pk=None):
        """Delete (deactivate) an SMS template"""
        instance = self.get_object()
        instance.is_active = False
        instance.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminSystemSMSTemplateViewSet(TainoAdminGenericViewSet):
    """
    Admin ViewSet for managing system SMS templates
    """

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["code", "name", "template_content", "description"]
    filterset_fields = ["is_active"]
    ordering_fields = ["name", "created_at", "updated_at"]
    ordering = ["name"]

    def get_queryset(self):
        """Get all system SMS templates"""
        return SystemSMSTemplate.objects.all()

    def get_serializer_class(self):
        """Select appropriate serializer based on action"""
        if self.action == "test_template":
            return AdminSystemTemplateTestSerializer
        return AdminSystemSMSTemplateSerializer

    @extend_schema(summary="List system SMS templates", description="Admin endpoint to list all system SMS templates")
    def list(self, request, *args, **kwargs):
        """List all system SMS templates"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Get system SMS template details",
        description="Admin endpoint to get details of a specific system SMS template",
    )
    def retrieve(self, request, pk=None):
        """Get details of a specific system SMS template"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(summary="Create system SMS template", description="Admin endpoint to create a new system SMS template")
    def create(self, request):
        """Create a new system SMS template"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        template = serializer.save()

        return Response(self.get_serializer(template).data, status=status.HTTP_201_CREATED)

    @extend_schema(summary="Update system SMS template", description="Admin endpoint to update a system SMS template")
    def update(self, request, pk=None):
        """Update a system SMS template"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        template = serializer.save()

        return Response(self.get_serializer(template).data)

    @extend_schema(
        summary="Partially update system SMS template", description="Admin endpoint to partially update a system SMS template"
    )
    def partial_update(self, request, pk=None):
        """Partially update a system SMS template"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        template = serializer.save()

        return Response(self.get_serializer(template).data)

    @extend_schema(
        summary="Initialize default templates",
        description="Initialize the default system SMS templates",
        responses={200: dict},
    )
    @action(detail=False, methods=["post"], url_path="initialize-defaults")
    def initialize_defaults(self, request):
        """Initialize the default system SMS templates"""
        # Initialize default templates
        SystemSMSTemplate.initialize_default_templates()

        # Count templates
        count = SystemSMSTemplate.objects.count()

        return Response(
            {"success": True, "message": f"Default templates initialized. {count} templates available.", "count": count}
        )

    @extend_schema(
        summary="Test template formatting",
        description="Test a system template with sample data",
        request=AdminSystemTemplateTestSerializer,
        responses={200: dict},
    )
    @action(detail=False, methods=["post"], url_path="test")
    def test_template(self, request):
        """Test a system template with sample data"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response(result)
