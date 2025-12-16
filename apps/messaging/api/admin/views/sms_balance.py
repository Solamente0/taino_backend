from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.messaging.api.admin.serializers import (
    AdminSMSBalanceSerializer,
    AdminSMSBalanceUpdateSerializer,
    AdminAddSMSBalanceSerializer,
    AdminBulkAddSMSBalanceSerializer,
    AdminLowBalanceUsersSerializer,
)
from apps.messaging.models import SMSBalance
from base_utils.views.admin import TainoAdminGenericViewSet

User = get_user_model()


class AdminSMSBalanceViewSet(TainoAdminGenericViewSet):
    """
    Admin ViewSet for managing users' SMS balances
    """

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["user__first_name", "user__last_name", "user__email", "user__phone_number"]
    filterset_fields = ["is_active"]
    ordering_fields = ["balance", "created_at", "updated_at"]
    ordering = ["-updated_at"]

    def get_queryset(self):
        """Get all SMS balances"""
        return SMSBalance.objects.all().select_related("user")

    def get_serializer_class(self):
        """Select appropriate serializer based on action"""
        if self.action == "partial_update":
            return AdminSMSBalanceUpdateSerializer
        elif self.action == "add_balance":
            return AdminAddSMSBalanceSerializer
        elif self.action == "bulk_add_balance":
            return AdminBulkAddSMSBalanceSerializer
        return AdminSMSBalanceSerializer

    @extend_schema(summary="List SMS balances", description="Admin endpoint to list all users' SMS balances")
    def list(self, request):
        """List all SMS balances"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Get SMS balance details", description="Admin endpoint to get details of a specific SMS balance record"
    )
    def retrieve(self, request, pk=None):
        """Get details of a specific SMS balance"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(summary="Update SMS balance", description="Admin endpoint to update a user's SMS balance")
    def partial_update(self, request, pk=None):
        """Update a user's SMS balance"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Store previous balance for logging
        previous_balance = instance.balance

        # Update balance
        balance = serializer.save()

        # Create admin action log if available
        try:
            from apps.admin_panel.models import AdminActionLog

            AdminActionLog.objects.create(
                admin_user=request.user,
                action_type="update_sms_balance",
                affected_user=instance.user,
                description=f"Updated SMS balance from {previous_balance} to {balance.balance}",
                data={"previous_balance": previous_balance, "new_balance": balance.balance, "is_active": balance.is_active},
            )
        except ImportError:
            # AdminActionLog not available, continue without logging
            pass

        return Response(AdminSMSBalanceSerializer(balance).data)

    @extend_schema(
        summary="Add balance to user",
        description="Add SMS credits to a specific user's balance",
        request=AdminAddSMSBalanceSerializer,
        responses={200: dict},
    )
    @action(detail=False, methods=["post"], url_path="add-balance")
    def add_balance(self, request):
        """Add SMS credits to a user's balance"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response(result)

    @extend_schema(
        summary="Add balance to multiple users",
        description="Add SMS credits to multiple users at once",
        request=AdminBulkAddSMSBalanceSerializer,
        responses={200: dict},
    )
    @action(detail=False, methods=["post"], url_path="bulk-add-balance")
    def bulk_add_balance(self, request):
        """Add SMS credits to multiple users at once"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response(result)

    @extend_schema(
        summary="Get users with low balance",
        description="Get a list of users with SMS balance below threshold",
        request=AdminLowBalanceUsersSerializer,
        responses={200: dict},
    )
    @action(detail=False, methods=["post"], url_path="low-balance-users")
    def low_balance_users(self, request):
        """Get users with SMS balance below threshold"""
        serializer = AdminLowBalanceUsersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response(result)
