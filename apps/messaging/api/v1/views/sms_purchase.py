from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.messaging.api.v1.serializers import SMSPurchaseSerializer, SMSPurchaseCreateSerializer
from apps.messaging.models import SMSPurchase
from base_utils.views.mobile import TainoMobileGenericViewSet
from apps.lawyer_office.permissions import SecretaryOrLawyerPermission


class SMSPurchaseViewSet(TainoMobileGenericViewSet):
    """
    ViewSet for SMS purchases

    Allows users to purchase SMS credits with coins and view purchase history.
    """

    permission_classes = [IsAuthenticated, SecretaryOrLawyerPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["purchase_date", "coins_spent", "sms_quantity"]
    ordering = ["-purchase_date"]

    def get_queryset(self):
        """Get purchase history for current user"""
        return SMSPurchase.objects.filter(user=self.request.user, is_active=True)

    def get_serializer_class(self):
        """Select appropriate serializer based on action"""
        if self.action == "create":
            return SMSPurchaseCreateSerializer
        return SMSPurchaseSerializer

    @extend_schema(
        summary="List SMS credit purchases",
        description="Returns a list of the user's SMS credit purchase history",
        responses={200: SMSPurchaseSerializer(many=True)},
    )
    def list(self, request):
        """
        List user's SMS purchases

        Returns purchase history for the authenticated user.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Purchase SMS credits",
        description="Purchase SMS credits using coins (10 SMS per coin)",
        request=SMSPurchaseCreateSerializer,
        responses={
            201: inline_serializer(
                name="SMSPurchaseResponseSerializer",
                fields={
                    "success": serializers.BooleanField(),
                    "coins_spent": serializers.IntegerField(),
                    "sms_quantity": serializers.IntegerField(),
                    "balance": serializers.IntegerField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def create(self, request):
        """
        Purchase SMS with coins

        Ctainoerts coins to SMS credits (1 coin = 10 SMS).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response(result, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Get purchase details",
        description="Get detailed information about a specific purchase",
        responses={200: SMSPurchaseSerializer},
    )
    def retrieve(self, request, pk=None):
        """Get details of a specific purchase"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
