from django.contrib.auth import get_user_model
from django.db.models import Sum, Count
from drf_spectacular.utils import extend_schema
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.messaging.api.admin.serializers import AdminSMSPurchaseSerializer
from apps.messaging.models import SMSPurchase
from base_utils.views.admin import TainoAdminGenericViewSet

User = get_user_model()


class AdminSMSPurchaseViewSet(TainoAdminGenericViewSet):
    """
    Admin ViewSet for managing SMS purchases
    """

    serializer_class = AdminSMSPurchaseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["user__first_name", "user__last_name", "user__email", "user__phone_number"]
    filterset_fields = ["is_active"]
    ordering_fields = ["purchase_date", "coins_spent", "sms_quantity"]
    ordering = ["-purchase_date"]

    def get_queryset(self):
        """Get all SMS purchases"""
        return SMSPurchase.objects.all().select_related("user")

    @extend_schema(summary="List SMS purchases", description="Admin endpoint to list all SMS purchases")
    def list(self, request):
        """List all SMS purchases"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(summary="Get SMS purchase details", description="Admin endpoint to get details of a specific SMS purchase")
    def retrieve(self, request, pk=None):
        """Get details of a specific SMS purchase"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(summary="Get purchase statistics", description="Get statistics on SMS purchases", responses={200: dict})
    @action(detail=False, methods=["get"], url_path="statistics")
    def statistics(self, request):
        """Get statistics on SMS purchases"""
        # Get all purchases
        purchases = SMSPurchase.objects.filter(is_active=True)

        # Total coins spent and SMS purchased
        total_coins = purchases.aggregate(Sum("coins_spent"))["coins_spent__sum"] or 0
        total_sms = purchases.aggregate(Sum("sms_quantity"))["sms_quantity__sum"] or 0

        # Purchases by month
        from django.db.models.functions import TruncMonth

        monthly_stats = (
            purchases.annotate(month=TruncMonth("purchase_date"))
            .values("month")
            .annotate(count=Count("id"), coins=Sum("coins_spent"), sms=Sum("sms_quantity"))
            .order_by("-month")
        )

        # Top users by purchases
        top_users = (
            purchases.values("user__pid", "user__first_name", "user__last_name")
            .annotate(count=Count("id"), coins=Sum("coins_spent"), sms=Sum("sms_quantity"))
            .order_by("-sms")[:10]
        )

        # Prepare response
        monthly_data = []
        for stat in monthly_stats:
            monthly_data.append(
                {
                    "month": stat["month"].strftime("%Y-%m") if stat["month"] else "Unknown",
                    "count": stat["count"],
                    "coins": stat["coins"],
                    "sms": stat["sms"],
                }
            )

        top_users_data = []
        for user in top_users:
            top_users_data.append(
                {
                    "user_id": user["user__pid"],
                    "name": f"{user['user__first_name']} {user['user__last_name']}".strip(),
                    "purchase_count": user["count"],
                    "coins_spent": user["coins"],
                    "sms_purchased": user["sms"],
                }
            )

        return Response(
            {
                "total_purchases": purchases.count(),
                "total_coins_spent": total_coins,
                "total_sms_purchased": total_sms,
                "monthly_stats": monthly_data,
                "top_users": top_users_data,
            }
        )
