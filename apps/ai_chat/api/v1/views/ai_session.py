# apps/ai_chat/api/v1/views.py
import logging

from django.db.models import Sum
from rest_framework import status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer

from apps.ai_chat.models import (
    AISession,
    AIMessage,
    ChatAIConfig,
    AIMessageTypeEnum,
    AISessionStatusEnum,
    GeneralChatAIConfig,
)
from base_utils.views.mobile import (
    TainoMobileGenericViewSet,
    TainoMobileRetrieveModelMixin,
    TainoMobileListModelMixin,
)

from apps.ai_chat.api.v1.serializers import (
    AISessionSerializer,
    AISessionDetailSerializer,
    ChatAIConfigSerializer,
    CreateAISessionSerializer,
    GeneralChatAIConfigSerializer,
)

logger = logging.getLogger(__name__)


class AISessionViewSet(TainoMobileListModelMixin, TainoMobileRetrieveModelMixin, TainoMobileGenericViewSet):
    """ViewSet for AI sessions"""

    serializer_class = AISessionSerializer

    def get_queryset(self):
        user = self.request.user
        return AISession.objects.filter(user=user, is_deleted=False).order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AISessionDetailSerializer
        return AISessionSerializer

    @extend_schema(responses={200: GeneralChatAIConfigSerializer(many=True)})
    @action(detail=False, methods=["get"], url_path="general-configs")
    def get_general_configs(self, request):
        """Get all general AI configurations (categories)"""
        configs = GeneralChatAIConfig.objects.filter(is_active=True).order_by("order")
        serializer = GeneralChatAIConfigSerializer(configs, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[OpenApiParameter(name="general_config_id", type=str, required=True)],
        responses={200: ChatAIConfigSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="ai-configs")
    def get_ai_configs(self, request):
        """Get AI configs for a specific general config"""
        general_config_id = request.query_params.get("general_config_id")

        if not general_config_id:
            return Response({"detail": "general_config_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        configs = ChatAIConfig.objects.filter(general_config__pid=general_config_id, is_active=True).order_by(
            "order", "strength"
        )

        serializer = ChatAIConfigSerializer(configs, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="general_static_name", type=str, required=False, description="Filter by general config static name"
            )
        ],
        responses={
            200: inline_serializer(
                name="AIConfigListResponseV2",
                fields={
                    "general_configs": GeneralChatAIConfigSerializer(many=True),
                    "ai_configs_by_general": serializers.DictField(),
                },
            )
        },
    )
    @action(detail=False, methods=["get"], url_path="configs-list")
    def get_configs_list(self, request):
        """Get AI configuration list with general configs and their related AI configs"""
        general_static_name = request.query_params.get("general_static_name")

        # Get general configs
        general_configs_query = GeneralChatAIConfig.objects.filter(is_active=True)

        if general_static_name:
            general_configs_query = general_configs_query.filter(static_name=general_static_name)

        general_configs = general_configs_query.order_by("order")

        # Prepare response data
        response_data = {
            "general_configs": GeneralChatAIConfigSerializer(general_configs, many=True).data,
            "ai_configs_by_general": {},
        }

        # Get AI configs for each general config
        for general_config in general_configs:
            ai_configs = (
                ChatAIConfig.objects.filter(general_config=general_config, is_active=True)
                .select_related("general_config", "related_service")
                .order_by("order", "strength")
            )

            response_data["ai_configs_by_general"][str(general_config.pid)] = ChatAIConfigSerializer(
                ai_configs, many=True
            ).data

        return Response(response_data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="general_static_name", type=str, required=False, description="Filter by general config static name"
            )
        ],
        responses={
            200: inline_serializer(
                name="AIConfigsNestedResponseV2",
                fields={
                    "pid": serializers.CharField(),
                    "name": serializers.CharField(),
                    "static_name": serializers.CharField(),
                    "description": serializers.CharField(),
                    "max_messages_per_chat": serializers.IntegerField(),
                    "max_tokens_per_chat": serializers.IntegerField(),
                    "order": serializers.IntegerField(),
                    "icon": serializers.CharField(),
                    "ai_configs": ChatAIConfigSerializer(many=True),
                },
                many=True,
            )
        },
    )
    @action(detail=False, methods=["get"], url_path="configs-nested")
    def get_configs_nested(self, request):
        """Get AI configuration list with nested structure and complete fields"""
        general_static_name = request.query_params.get("general_static_name")

        # Get general configs
        general_configs_query = GeneralChatAIConfig.objects.filter(is_active=True)

        if general_static_name:
            general_configs_query = general_configs_query.filter(static_name=general_static_name)

        general_configs = general_configs_query.order_by("order")

        # Build nested response
        response_data = []
        for general_config in general_configs:
            ai_configs = (
                ChatAIConfig.objects.filter(general_config=general_config, is_active=True)
                .select_related("general_config", "related_service")
                .order_by("order", "strength")
            )

            response_data.append(
                {
                    "pid": str(general_config.pid),
                    "name": general_config.name,
                    "static_name": general_config.static_name,
                    "description": general_config.description,
                    "icon": general_config.icon.url if general_config.icon else None,
                    "max_messages_per_chat": general_config.max_messages_per_chat,
                    "max_tokens_per_chat": general_config.max_tokens_per_chat,
                    "order": general_config.order,
                    "created_at": general_config.created_at,
                    "updated_at": general_config.updated_at,
                    "is_active": general_config.is_active,
                    "ai_configs": ChatAIConfigSerializer(ai_configs, many=True).data,
                }
            )

        return Response(response_data)

    @extend_schema(request=CreateAISessionSerializer, responses={200: AISessionDetailSerializer})
    @action(detail=False, methods=["post"], url_path="create")
    def create_session(self, request):
        """Create a new AI chat session"""
        serializer = CreateAISessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        ai_config = serializer.validated_data["ai_config"]
        title = (
            serializer.validated_data.get("title") or f"{ai_config.general_config.name} - {ai_config.get_strength_display()}"
        )
        temperature = serializer.validated_data.get("default_temperature", ai_config.default_temperature)
        max_tokens = serializer.validated_data.get("default_max_tokens", ai_config.default_max_tokens)

        try:
            # Create session
            ai_session = AISession.objects.create(
                user=user,
                ai_config=ai_config,
                status=AISessionStatusEnum.ACTIVE,
                title=title,
                temperature=temperature,
                max_tokens=max_tokens,
                creator=user,
                ai_context={
                    "config_id": str(ai_config.pid),
                    "general_config_id": str(ai_config.general_config.pid),
                    "model_name": ai_config.model_name,
                    "strength": ai_config.strength,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )

            # Create welcome message
            AIMessage.objects.create(
                ai_session=ai_session,
                sender=user,
                content=f"سلام! من {ai_config.name} هستم. چطور می‌تونم کمکتون کنم؟",
                message_type=AIMessageTypeEnum.TEXT,
                is_ai=True,
                is_system=True,
            )

            response_serializer = AISessionDetailSerializer(ai_session)
            return Response(response_serializer.data)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={200: AISessionSerializer(many=True)})
    @action(detail=False, methods=["get"], url_path="my-sessions")
    def my_sessions(self, request):
        """Get all AI sessions for the user"""
        queryset = self.filter_queryset(self.get_queryset())

        status_param = request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        ai_type_param = request.query_params.get("ai_type")
        if ai_type_param:
            queryset = queryset.filter(ai_type=ai_type_param)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        responses={
            200: inline_serializer(
                name="SessionTransactionSummary",
                fields={
                    "session_pid": serializers.CharField(),
                    "pricing_type": serializers.CharField(),
                    "total_messages": serializers.IntegerField(),
                    "total_cost_coins": serializers.FloatField(),
                    "total_input_tokens": serializers.IntegerField(),
                    "total_output_tokens": serializers.IntegerField(),
                    "total_tokens_used": serializers.IntegerField(),
                    "average_cost_per_message": serializers.FloatField(),
                },
            )
        }
    )
    @action(detail=True, methods=["get"], url_path="transaction-summary")
    def transaction_summary(self, request, pid=None):
        """Get transaction summary for this session"""
        try:
            ai_session = self.get_object()

            # Check permissions
            if request.user != ai_session.user:
                return Response(
                    {"detail": "You don't have permission to view this session"}, status=status.HTTP_403_FORBIDDEN
                )

            summary = ai_session.get_transaction_summary()
            return Response(summary)

        except AISession.DoesNotExist:
            return Response({"detail": "Session not found"}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        responses={
            200: inline_serializer(
                name="EstimatedCost",
                fields={
                    "estimated_cost": serializers.FloatField(),
                    "pricing_type": serializers.CharField(),
                    "currency": serializers.CharField(),
                },
            )
        }
    )
    @action(detail=True, methods=["get"], url_path="estimated-cost")
    def estimated_cost(self, request, pid=None):
        """Get estimated cost for next message"""
        try:
            ai_session = self.get_object()

            # Check permissions
            if request.user != ai_session.user:
                return Response(
                    {"detail": "You don't have permission to view this session"}, status=status.HTTP_403_FORBIDDEN
                )

            estimate = ai_session.calculate_estimated_next_cost()
            return Response(estimate)

        except AISession.DoesNotExist:
            return Response({"detail": "Session not found"}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        responses={
            200: inline_serializer(
                name="UserAIStatistics",
                fields={
                    "total_sessions": serializers.IntegerField(),
                    "total_messages": serializers.IntegerField(),
                    "total_spent_coins": serializers.FloatField(),
                    "average_cost_per_session": serializers.FloatField(),
                    "average_messages_per_session": serializers.FloatField(),
                    "by_pricing_type": serializers.DictField(),
                },
            )
        }
    )
    @action(detail=False, methods=["get"], url_path="my-statistics")
    def my_statistics(self, request):
        """Get user's AI usage statistics"""
        user = request.user

        sessions = AISession.objects.filter(user=user, is_deleted=False)

        # Overall stats
        total_sessions = sessions.count()
        total_messages = sessions.aggregate(Sum("total_messages"))["total_messages__sum"] or 0
        total_spent = sessions.aggregate(Sum("total_cost_coins"))["total_cost_coins__sum"] or 0

        avg_cost_per_session = float(total_spent) / total_sessions if total_sessions > 0 else 0
        avg_messages_per_session = total_messages / total_sessions if total_sessions > 0 else 0

        # Stats by pricing type
        by_pricing_type = {}
        for pricing_type in ["message_based", "token_based"]:
            type_sessions = sessions.filter(ai_config__pricing_type=pricing_type)
            type_count = type_sessions.count()

            if type_count > 0:
                type_messages = type_sessions.aggregate(Sum("total_messages"))["total_messages__sum"] or 0
                type_cost = type_sessions.aggregate(Sum("total_cost_coins"))["total_cost_coins__sum"] or 0

                by_pricing_type[pricing_type] = {
                    "sessions": type_count,
                    "messages": type_messages,
                    "total_cost": float(type_cost),
                    "avg_cost_per_message": float(type_cost) / type_messages if type_messages > 0 else 0,
                }

        return Response(
            {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "total_spent_coins": float(total_spent),
                "average_cost_per_session": avg_cost_per_session,
                "average_messages_per_session": avg_messages_per_session,
                "by_pricing_type": by_pricing_type,
            }
        )

    @extend_schema(
        parameters=[OpenApiParameter(name="limit", type=int, required=False, default=10)],
        responses={
            200: inline_serializer(
                name="SessionTransactions",
                fields={
                    "session_pid": serializers.CharField(),
                    "transactions": serializers.ListField(),
                    "total_transactions": serializers.IntegerField(),
                },
            )
        },
    )
    @action(detail=True, methods=["get"], url_path="transactions")
    def session_transactions(self, request, pid=None):
        """Get all wallet transactions for this session"""
        try:
            from apps.wallet.models import Transaction as WalletTransaction

            ai_session = self.get_object()

            # Check permissions
            if request.user != ai_session.user:
                return Response(
                    {"detail": "You don't have permission to view this session"}, status=status.HTTP_403_FORBIDDEN
                )

            limit = int(request.query_params.get("limit", 10))

            # Get transactions that match this session
            transactions = WalletTransaction.objects.filter(
                user=ai_session.user, reference_id__startswith=f"ai_msg_{ai_session.pid}_"
            ).order_by("-created_at")[:limit]

            transaction_data = []
            for txn in transactions:
                transaction_data.append(
                    {
                        "id": str(txn.pid) if hasattr(txn, "pid") else txn.id,
                        "amount": float(txn.coin_amount),
                        "description": txn.description,
                        "reference_id": txn.reference_id,
                        "created_at": txn.created_at.isoformat(),
                    }
                )

            return Response(
                {
                    "session_pid": str(ai_session.pid),
                    "transactions": transaction_data,
                    "total_transactions": len(transaction_data),
                }
            )

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    #
    # @extend_schema(
    #     request=inline_serializer(
    #         name="CreateAISessionSerializer",
    #         fields={
    #             "title": serializers.CharField(required=False, allow_null=True),
    #             "ai_type": serializers.CharField(required=False, allow_null=True),
    #             "duration_minutes": serializers.IntegerField(required=False, default=6),
    #             "use_coins": serializers.BooleanField(required=False, default=True),
    #         },
    #     ),
    #     responses={200: AISessionDetailSerializer},
    # )
    # @action(detail=False, methods=["post"], url_path="create")
    # def create_session(self, request):
    #     """Create a new AI chat session"""
    #     user = request.user
    #     title = request.data.get("title", _("AI Consultation"))
    #     ai_type = request.data.get("ai_type", "v")
    #     duration_minutes = GeneralSettingsQuery.get_ai_chat_duration()
    #     use_coins = request.data.get("use_coins", True)
    #
    #     try:
    #         # Charge the user
    #         charge_success = AIChatService.charge_for_ai_chat(
    #             user=user, ai_type=ai_type, duration_minutes=duration_minutes, use_coins=use_coins
    #         )
    #
    #         if not charge_success:
    #             if use_coins:
    #                 price = GeneralSettingsQuery.get_ai_chat_price_by_type(ai_type)
    #                 return Response(
    #                     {
    #                         "detail": _("موجودی سکه شما کافی نیست. لطفا کیف پول خود را شارژ کنید."),
    #                         "required_coins": price,
    #                     },
    #                     status=status.HTTP_400_BAD_REQUEST,
    #                 )
    #             else:
    #                 return Response(
    #                     {"detail": _("Insufficient balance. Please add funds to your wallet.")},
    #                     status=status.HTTP_400_BAD_REQUEST,
    #                 )
    #
    #         # Create session
    #         ai_session = AIChatService.create_ai_session(
    #             user=user, ai_type=ai_type, title=title, duration_minutes=duration_minutes, use_coins=use_coins
    #         )
    #
    #         if not ai_session:
    #             return Response(
    #                 {"detail": _("Failed to create AI session")},
    #                 status=status.HTTP_400_BAD_REQUEST,
    #             )
    #
    #         # Create welcome message
    #         ai_type_display = {"v": "V", "v_plus": "V+", "v_x": "VX"}.get(ai_type, ai_type.upper())
    #
    #         AIChatService.send_message(
    #             ai_session=ai_session,
    #             sender=user,
    #             content=f"سلام به هوش مصنوعی {ai_type_display} خوش اومدی. چه کمکی از من ساخته است؟",
    #             message_type="text",
    #             is_ai=True,
    #             is_system=True,
    #         )
    #
    #         serializer = AISessionDetailSerializer(ai_session)
    #         return Response(serializer.data)
    #
    #     except Exception as e:
    #         return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    #
    # @extend_schema(
    #     request=inline_serializer(
    #         name="ExtendAISessionSerializer",
    #         fields={
    #             "additional_minutes": serializers.IntegerField(required=True),
    #             "use_coins": serializers.BooleanField(required=False, default=False),
    #         },
    #     ),
    #     responses={200: AISessionDetailSerializer},
    # )
    # @action(detail=True, methods=["post"], url_path="extend")
    # def extend_session(self, request, pid=None):
    #     """Extend an AI session's duration"""
    #     try:
    #         ai_session = AISession.objects.get(pid=pid, user=request.user, is_deleted=False)
    #
    #         if ai_session.status != "active":
    #             return Response(
    #                 {"detail": _("Cannot extend an inactive AI session")},
    #                 status=status.HTTP_400_BAD_REQUEST,
    #             )
    #
    #         if ai_session.end_date and ai_session.end_date < timezone.now():
    #             return Response(
    #                 {"detail": _("This AI session has already expired")},
    #                 status=status.HTTP_400_BAD_REQUEST,
    #             )
    #
    #         additional_minutes = request.data.get("additional_minutes", 0)
    #         if additional_minutes <= 0:
    #             return Response(
    #                 {"detail": _("Additional minutes must be greater than 0")},
    #                 status=status.HTTP_400_BAD_REQUEST,
    #             )
    #
    #         use_coins = request.data.get("use_coins", False)
    #
    #         success = AIChatService.extend_ai_session(
    #             ai_session=ai_session, additional_minutes=additional_minutes, use_coins=use_coins
    #         )
    #
    #         if not success:
    #             if use_coins:
    #                 price = GeneralSettingsQuery.get_ai_chat_price_by_type(ai_session.ai_type)
    #                 return Response(
    #                     {
    #                         "detail": _("موجودی سکه شما کافی نیست. لطفا کیف پول خود را شارژ کنید."),
    #                         "required_coins": price,
    #                     },
    #                     status=status.HTTP_400_BAD_REQUEST,
    #                 )
    #             else:
    #                 return Response(
    #                     {"detail": _("Insufficient balance. Please add funds to your wallet.")},
    #                     status=status.HTTP_400_BAD_REQUEST,
    #                 )
    #
    #         serializer = AISessionDetailSerializer(ai_session)
    #         return Response(serializer.data)
    #
    #     except AISession.DoesNotExist:
    #         return Response({"detail": _("AI session not found")}, status=status.HTTP_404_NOT_FOUND)
    #     except Exception as e:
    #         return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    #
    # @extend_schema(responses={200: AISessionSerializer(many=True)})
    # @action(detail=False, methods=["get"], url_path="expired")
    # def expired_sessions(self, request):
    #     """Get expired AI sessions"""
    #     user = request.user
    #     now = timezone.now()
    #
    #     queryset = AISession.objects.filter(
    #         user=user,
    #         is_deleted=False,
    #         end_date__lt=now,
    #         status="active",
    #     ).order_by("-end_date")
    #
    #     if queryset.exists():
    #         queryset.update(status="expired")
    #
    #     page = self.paginate_queryset(queryset)
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True)
    #         return self.get_paginated_response(serializer.data)
    #
    #     serializer = self.get_serializer(queryset, many=True)
    #     return Response(serializer.data)

    @extend_schema(responses={200: ChatAIConfigSerializer(many=True)})
    @action(detail=False, methods=["get"], url_path="ai-types")
    def get_ai_types(self, request):
        """Get available AI types"""
        configs = ChatAIConfig.objects.filter(is_active=True)
        serializer = ChatAIConfigSerializer(configs, many=True)
        return Response(serializer.data)
