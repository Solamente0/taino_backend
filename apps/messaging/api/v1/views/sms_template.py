from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.messaging.api.v1.serializers import (
    SMSTemplateSerializer,
    SMSTemplateCreateUpdateSerializer,
    SystemSMSTemplateSerializer,
)
from apps.messaging.models import SMSTemplate, SystemSMSTemplate
from apps.messaging.services.utils import format_sms_template
from base_utils.views.mobile import TainoMobileGenericViewSet
from apps.lawyer_office.permissions import SecretaryOrLawyerPermission


class SMSTemplateViewSet(TainoMobileGenericViewSet):
    """
    ViewSet for managing SMS templates

    Allows creating, viewing, updating, and deleting custom SMS templates.
    System templates can only be viewed, not modified.
    """

    permission_classes = [IsAuthenticated, SecretaryOrLawyerPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "content"]
    filterset_fields = ["template_type", "is_system"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        Get available templates for current user

        Returns system templates and the user's own custom templates.
        """
        return SMSTemplate.objects.filter(is_active=True).filter(Q(is_system=True) | Q(creator=self.request.user))

    def get_serializer_class(self):
        """Select appropriate serializer based on action"""
        if self.action in ["create", "update", "partial_update"]:
            return SMSTemplateCreateUpdateSerializer
        return SMSTemplateSerializer

    @extend_schema(
        summary="List available SMS templates",
        description="Returns a list of all available templates, including system templates and user's custom templates",
        responses={200: SMSTemplateSerializer(many=True)},
    )
    def list(self, request):
        """List available SMS templates"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create a new SMS template",
        description="Create a new custom SMS template with placeholders for dynamic content",
        request=SMSTemplateCreateUpdateSerializer,
        responses={201: SMSTemplateSerializer},
    )
    def create(self, request):
        """
        Create a new SMS template

        Creates a custom template that can be used for sending messages.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        template = serializer.save()

        return Response(
            SMSTemplateSerializer(template, context=self.get_serializer_context()).data, status=status.HTTP_201_CREATED
        )

    @extend_schema(
        summary="Get template details",
        description="Get detailed information about a specific template",
        responses={200: SMSTemplateSerializer},
    )
    def retrieve(self, request, pk=None):
        """Get details of a specific template"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        summary="Update an SMS template",
        description="Update an existing custom template (system templates cannot be modified)",
        request=SMSTemplateCreateUpdateSerializer,
        responses={200: SMSTemplateSerializer},
    )
    def update(self, request, pk=None):
        """
        Update an SMS template

        System templates cannot be modified.
        """
        instance = self.get_object()

        # Prevent updating system templates
        if instance.is_system:
            return Response({"detail": _("System templates cannot be modified")}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        template = serializer.save()

        return Response(SMSTemplateSerializer(template, context=self.get_serializer_context()).data)

    @extend_schema(
        summary="Partially update an SMS template",
        description="Update specific fields of an existing custom template",
        request=SMSTemplateCreateUpdateSerializer,
        responses={200: SMSTemplateSerializer},
    )
    def partial_update(self, request, pk=None):
        """
        Partially update an SMS template

        System templates cannot be modified.
        """
        instance = self.get_object()

        # Prevent updating system templates
        if instance.is_system:
            return Response({"detail": _("System templates cannot be modified")}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        template = serializer.save()

        return Response(SMSTemplateSerializer(template, context=self.get_serializer_context()).data)

    @extend_schema(
        summary="Delete an SMS template", description="Delete (deactivate) a custom SMS template", responses={204: None}
    )
    def destroy(self, request, pk=None):
        """
        Delete an SMS template

        Performs a soft delete by marking as inactive.
        System templates cannot be deleted.
        """
        instance = self.get_object()

        # Prevent deleting system templates
        if instance.is_system:
            return Response({"detail": _("System templates cannot be deleted")}, status=status.HTTP_403_FORBIDDEN)

        instance.is_active = False
        instance.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Test template formatting",
        description="Preview how a template will look with sample data",
        request=inline_serializer(
            name="TemplateTestSerializer",
            fields={"context": serializers.DictField()},
        ),
        responses={
            200: inline_serializer(
                name="TemplateTestResponseSerializer",
                fields={
                    "success": serializers.BooleanField(),
                    "formatted_message": serializers.CharField(),
                    "error": serializers.CharField(allow_null=True),
                },
            )
        },
    )
    @action(detail=True, methods=["post"], url_path="test")
    def test_template(self, request, pk=None):
        """
        Test a template with custom values

        Allows testing how the template will look when formatted with data.
        """
        instance = self.get_object()
        context = request.data.get("context", {})

        # Format the template
        success, formatted_message, error = format_sms_template(instance.code, context)

        return Response({"success": success, "formatted_message": formatted_message, "error": error})


class SystemSMSTemplateViewSet(TainoMobileGenericViewSet):
    """
    ViewSet for system SMS templates

    Provides read-only access to system-defined SMS templates.
    """

    serializer_class = SystemSMSTemplateSerializer
    permission_classes = [IsAuthenticated, SecretaryOrLawyerPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["name", "code", "template_content"]

    def get_queryset(self):
        """Get active system templates"""
        return SystemSMSTemplate.objects.filter(is_active=True)

    @extend_schema(
        summary="List system templates",
        description="Returns a list of all available system SMS templates",
        responses={200: SystemSMSTemplateSerializer(many=True)},
    )
    def list(self, request):
        """
        List available system SMS templates

        Returns all active system-defined templates.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Get system template details",
        description="Get detailed information about a specific system template",
        responses={200: SystemSMSTemplateSerializer},
    )
    def retrieve(self, request, pk=None):
        """Get details of a system SMS template"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        summary="Preview template with sample data",
        description="Preview how a system template will look with sample data",
        responses={
            200: inline_serializer(
                name="TemplatePreviewSerializer",
                fields={
                    "template": SystemSMSTemplateSerializer(),
                    "sample_context": serializers.DictField(),
                    "preview": serializers.CharField(),
                },
            )
        },
    )
    @action(detail=True, methods=["get"], url_path="preview")
    def preview_template(self, request, pk=None):
        """
        Preview a system template with sample data

        Shows how the template looks when formatted with sample values.
        """
        template = self.get_object()

        # Create sample context based on template type
        sample_context = {}

        if template.code == "court_session_reminder":
            sample_context = {
                "date": "1402/05/15",
                "time": "10:00",
                "court_branch": "شعبه 5 دادگاه",
                "client_name": "علی محمدی",
            }
        elif template.code == "objection_deadline_reminder":
            sample_context = {
                "objection_type": "رای دادگاه",
                "case_subject": "دعوی حقوقی شماره 15/1402",
                "client_name": "علی محمدی",
            }
        elif template.code == "exchange_deadline_reminder":
            sample_context = {
                "exchange_type": "تبادل لایحه",
                "case_subject": "دعوی حقوقی شماره 15/1402",
                "client_name": "علی محمدی",
            }

        # Format template with sample context
        success, preview_text, error = format_sms_template(template.code, sample_context)

        if not success:
            preview_text = f"Error formatting template: {error}"

        return Response(
            {
                "template": SystemSMSTemplateSerializer(template).data,
                "sample_context": sample_context,
                "preview": preview_text,
            }
        )
