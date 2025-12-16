from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.messaging.api.admin.serializers import AdminLowBalanceUsersSerializer
from apps.messaging.models import SMSBalance, SMSMessage, SMSPurchase
from base_utils.views.admin import TainoAdminGenericViewSet

User = get_user_model()


class AdminSMSDashboardViewSet(TainoAdminGenericViewSet):
    """
    Admin ViewSet for SMS dashboard
    """

    @extend_schema(
        summary="Get SMS dashboard data", description="Get summary data for the SMS dashboard", responses={200: dict}
    )
    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        """Get summary data for the SMS dashboard"""
        # Total balances
        total_balance = SMSBalance.objects.filter(is_active=True).aggregate(Sum("balance"))["balance__sum"] or 0

        # Total messages
        total_messages = SMSMessage.objects.count()
        sent_messages = SMSMessage.objects.filter(status="sent").count()
        failed_messages = SMSMessage.objects.filter(status="failed").count()

        # Today's messages
        today = timezone.now().date()
        today_messages = SMSMessage.objects.filter(created_at__date=today).count()
        today_sent = SMSMessage.objects.filter(status="sent", created_at__date=today).count()

        # This month's messages
        first_day_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_messages = SMSMessage.objects.filter(created_at__gte=first_day_of_month).count()
        month_sent = SMSMessage.objects.filter(status="sent", created_at__gte=first_day_of_month).count()

        # Total purchases
        total_purchases = SMSPurchase.objects.filter(is_active=True).count()
        total_coins_spent = SMSPurchase.objects.filter(is_active=True).aggregate(Sum("coins_spent"))["coins_spent__sum"] or 0
        total_sms_purchased = (
            SMSPurchase.objects.filter(is_active=True).aggregate(Sum("sms_quantity"))["sms_quantity__sum"] or 0
        )

        # Users with SMS balance
        users_with_balance = SMSBalance.objects.filter(is_active=True, balance__gt=0).count()
        users_with_no_balance = SMSBalance.objects.filter(is_active=True, balance=0).count()

        # Daily message trend for last 30 days
        from django.db.models.functions import TruncDate

        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=30)

        daily_trend = (
            SMSMessage.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
            .annotate(date=TruncDate("created_at"))
            .values("date", "status")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        # Process daily trend
        daily_data = {}
        for item in daily_trend:
            date_str = item["date"].strftime("%Y-%m-%d")
            if date_str not in daily_data:
                daily_data[date_str] = {"sent": 0, "failed": 0, "pending": 0, "insufficient_balance": 0}
            daily_data[date_str][item["status"]] = item["count"]

        # Ctainoert to list format
        daily_trend_list = []
        for date_str, data in daily_data.items():
            daily_trend_list.append(
                {
                    "date": date_str,
                    "sent": data["sent"],
                    "failed": data["failed"],
                    "pending": data["pending"],
                    "insufficient_balance": data["insufficient_balance"],
                    "total": sum(data.values()),
                }
            )

        # Sort by date
        daily_trend_list.sort(key=lambda x: x["date"])

        return Response(
            {
                "total_balance": total_balance,
                "message_counts": {
                    "total": total_messages,
                    "sent": sent_messages,
                    "failed": failed_messages,
                    "success_rate": round((sent_messages / total_messages * 100) if total_messages > 0 else 0, 2),
                },
                "today": {
                    "total": today_messages,
                    "sent": today_sent,
                    "success_rate": round((today_sent / today_messages * 100) if today_messages > 0 else 0, 2),
                },
                "this_month": {
                    "total": month_messages,
                    "sent": month_sent,
                    "success_rate": round((month_sent / month_messages * 100) if month_messages > 0 else 0, 2),
                },
                "purchases": {
                    "count": total_purchases,
                    "coins_spent": total_coins_spent,
                    "sms_purchased": total_sms_purchased,
                },
                "users": {
                    "with_balance": users_with_balance,
                    "with_no_balance": users_with_no_balance,
                    "total": users_with_balance + users_with_no_balance,
                },
                "daily_trend": daily_trend_list,
            }
        )

    @extend_schema(
        summary="Get low balance users",
        description="Get users with low SMS balance",
        request=AdminLowBalanceUsersSerializer,
        responses={200: dict},
    )
    @action(detail=False, methods=["post"], url_path="low-balance-users")
    def low_balance_users(self, request):
        """Get users with low SMS balance"""
        serializer = AdminLowBalanceUsersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response(result)

    @extend_schema(summary="Get top users", description="Get top users by SMS usage", responses={200: dict})
    @action(detail=False, methods=["get"], url_path="top-users")
    def top_users(self, request):
        """Get top users by SMS usage"""
        # Top senders
        top_senders = (
            SMSMessage.objects.filter(status="sent")
            .values("sender__pid", "sender__first_name", "sender__last_name")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        # Top purchasers
        top_purchasers = (
            SMSPurchase.objects.filter(is_active=True)
            .values("user__pid", "user__first_name", "user__last_name")
            .annotate(count=Count("id"), total_coins=Sum("coins_spent"), total_sms=Sum("sms_quantity"))
            .order_by("-total_sms")[:10]
        )

        # Top balances
        top_balances = (
            SMSBalance.objects.filter(is_active=True)
            .values("user__pid", "user__first_name", "user__last_name", "balance")
            .order_by("-balance")[:10]
        )

        # Format response
        top_senders_data = []
        for sender in top_senders:
            top_senders_data.append(
                {
                    "user_id": sender["sender__pid"],
                    "name": f"{sender['sender__first_name']} {sender['sender__last_name']}".strip(),
                    "message_count": sender["count"],
                }
            )

        top_purchasers_data = []
        for purchaser in top_purchasers:
            top_purchasers_data.append(
                {
                    "user_id": purchaser["user__pid"],
                    "name": f"{purchaser['user__first_name']} {purchaser['user__last_name']}".strip(),
                    "purchase_count": purchaser["count"],
                    "coins_spent": purchaser["total_coins"],
                    "sms_purchased": purchaser["total_sms"],
                }
            )

        top_balances_data = []
        for balance in top_balances:
            top_balances_data.append(
                {
                    "user_id": balance["user__pid"],
                    "name": f"{balance['user__first_name']} {balance['user__last_name']}".strip(),
                    "balance": balance["balance"],
                }
            )

        return Response(
            {"top_senders": top_senders_data, "top_purchasers": top_purchasers_data, "top_balances": top_balances_data}
        )
