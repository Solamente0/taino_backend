# apps/wallet/admin.py
import jdatetime
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count, Q
from django.urls import reverse
from django.utils.safestring import mark_safe

from apps.common.apps import JalaliDateFieldListFilter
from apps.wallet.models import Wallet, Transaction, CoinSettings, CoinPackage


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """Admin interface for Wallet model"""

    list_display = [
        "user_info",
        "balance_display",
        "coin_balance_display",
        "currency",
        "is_active",
        "created_at",
        "actions_column",
    ]
    list_filter = ["is_active", "currency", "created_at"]
    search_fields = [
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__phone_number",
        "pid",
    ]
    readonly_fields = [
        "pid",
        "created_at",
        "updated_at",
        # "balance_display",
        # "coin_balance_display",
        "transaction_summary",
    ]
    fieldsets = (
        (
            _("اطلاعات کاربر"),
            {
                "fields": ("user", "pid"),
            },
        ),
        (
            _("موجودی"),
            {
                "fields": (
                    "balance",  # Make it editable
                    "coin_balance",  # Make it editable
                    "currency",
                ),
            },
        ),
        (
            _("وضعیت"),
            {
                "fields": ("is_active",),
            },
        ),
        (
            _("خلاصه تراکنش‌ها"),
            {
                "fields": ("transaction_summary",),
                "classes": ("collapse",),
            },
        ),
        (
            _("تاریخ‌ها"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def user_info(self, obj):
        """Display user information with link"""
        if obj.user:
            # FIX: Use the correct URL pattern name
            try:
                url = reverse("admin:authentication_tainouser_change", args=[obj.user.id])
            except:
                # Fallback to default user change URL
                url = reverse("admin:auth_user_change", args=[obj.user.id])

            role_badge = ""
            if hasattr(obj.user, "role") and obj.user.role:
                role_badge = f'<span style="background: #e3f2fd; color: #1976d2; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-right: 5px;">{obj.user.role.name}</span>'
            return format_html(
                '{}<a href="{}" style="text-decoration: none;">{}</a><br/>' '<small style="color: #666;">{}</small>',
                mark_safe(role_badge),
                url,
                obj.user.get_full_name() or "بدون نام",
                obj.user.email or obj.user.phone_number or "-",
            )
        return "-"

    user_info.short_description = _("کاربر")

    def balance_display(self, obj):
        """Display balance with formatting"""
        # FIX: Format numbers before passing to format_html
        formatted_balance = f"{int(obj.balance):,}"
        color = "#4caf50" if obj.balance > 0 else "#666"
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 14px;">{}</span> <small>ریال</small>',
            color,
            formatted_balance,
        )

    balance_display.short_description = _("موجودی ریالی")

    def coin_balance_display(self, obj):
        """Display coin balance with formatting"""
        # FIX: Format numbers before passing to format_html
        formatted_coin_balance = f"{int(obj.coin_balance):,}"
        color = "#ff9800" if obj.coin_balance > 0 else "#666"
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 14px;">{}</span> <small>سکه</small>',
            color,
            formatted_coin_balance,
        )

    coin_balance_display.short_description = _("موجودی سکه")

    def transaction_summary(self, obj):
        """Display transaction summary"""
        transactions = obj.transactions.all()
        total_transactions = transactions.count()

        deposits = transactions.filter(type="deposit", status="completed").aggregate(total=Sum("amount"))["total"] or 0
        withdrawals = transactions.filter(type="withdrawal", status="completed").aggregate(total=Sum("amount"))["total"] or 0
        coin_purchases = (
            transactions.filter(type="coin_purchase", status="completed").aggregate(total=Sum("coin_amount"))["total"] or 0
        )
        coin_usage = (
            transactions.filter(type="coin_usage", status="completed").aggregate(total=Sum("coin_amount"))["total"] or 0
        )

        # FIX: Format all numbers before passing to format_html
        return format_html(
            """
            <div style="background: #f5f5f5; padding: 15px; border-radius: 5px;">
                <div style="margin-bottom: 10px;">
                    <strong>تعداد کل تراکنش‌ها:</strong> <span style="color: #2196f3;">{}</span>
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>مجموع واریزی‌ها:</strong> <span style="color: #4caf50;">{} ریال</span>
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>مجموع برداشت‌ها:</strong> <span style="color: #f44336;">{} ریال</span>
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>مجموع خرید سکه:</strong> <span style="color: #ff9800;">{} سکه</span>
                </div>
                <div>
                    <strong>مجموع استفاده از سکه:</strong> <span style="color: #9c27b0;">{} سکه</span>
                </div>
            </div>
            """,
            total_transactions,
            f"{int(deposits):,}",
            f"{int(withdrawals):,}",
            f"{int(coin_purchases):,}",
            f"{int(coin_usage):,}",
        )

    transaction_summary.short_description = _("خلاصه تراکنش‌ها")

    def actions_column(self, obj):
        """Display action buttons"""
        transactions_url = reverse("admin:wallet_transaction_changelist") + f"?wallet__id__exact={obj.id}"
        return format_html(
            '<a href="{}" style="background: #2196f3; color: white; padding: 5px 10px; '
            'border-radius: 3px; text-decoration: none; font-size: 12px;">مشاهده تراکنش‌ها</a>',
            transactions_url,
        )

    actions_column.short_description = _("عملیات")

    def has_add_permission(self, request):
        """Prevent manual wallet creation"""
        return True


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin interface for Transaction model"""

    list_display = [
        "transaction_info",
        "wallet_user",
        "amount_display",
        "coin_amount_display",
        "type_badge",
        "status_badge",
        "created_at_jalali",
    ]
    list_filter = [
        "type",
        "status",
        "created_at",
        ("wallet__user__role", admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        "pid",
        "reference_id",
        "description",
        "wallet__user__first_name",
        "wallet__user__last_name",
        "wallet__user__email",
        "wallet__user__phone_number",
    ]
    readonly_fields = [
        "pid",
        "wallet",
        "amount",
        "coin_amount",
        "sms_amount",
        "type",
        "status",
        "exchange_rate",
        "reference_id",
        "metadata_display",
        "created_at_jalali",
        "updated_at",
        "user_statistics",  # آمار این کاربر
        "all_transactions_statistics",  # آمار کل تراکنش‌ها
    ]
    fieldsets = (
        (
            _("اطلاعات پایه"),
            {
                "fields": ("pid", "wallet", "type", "status"),
            },
        ),
        (
            _("مبالغ"),
            {
                "fields": ("amount", "coin_amount", "sms_amount", "exchange_rate"),
            },
        ),
        (
            _("جزئیات"),
            {
                "fields": ("description", "reference_id", "metadata_display"),
            },
        ),
        (
            _("آمار کاربر"),
            {
                "fields": ("user_statistics",),
                "classes": ("wide",),
            },
        ),
        (
            _("آمار کل سیستم"),
            {
                "fields": ("all_transactions_statistics",),
                "classes": ("wide", "collapse"),
            },
        ),
        (
            _("تاریخ‌ها"),
            {
                "fields": ("created_at_jalali", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
    date_hierarchy = "created_at"

    def transaction_info(self, obj):
        """نمایش بخشی از توضیحات"""
        if obj.description:
            desc_short = obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
            return format_html(
                '<span style="color: #555;">{}</span>',
                desc_short,
            )
        return format_html('<span style="color: #999;">-</span>')

    transaction_info.short_description = _("توضیحات")

    def created_at_jalali(self, obj):
        """نمایش تاریخ به شمسی"""
        if obj.created_at:
            jalali_date = jdatetime.datetime.fromgregorian(datetime=obj.created_at)
            formatted_date = jalali_date.strftime("%Y/%m/%d")
            formatted_time = jalali_date.strftime("%H:%M")

            return format_html(
                '<div style="direction: ltr;">'
                '<strong style="color: #2196f3;">{}</strong><br/>'
                '<small style="color: #666;">{}</small>'
                "</div>",
                formatted_date,
                formatted_time,
            )
        return "-"

    created_at_jalali.short_description = _("تاریخ تراکنش")
    created_at_jalali.admin_order_field = "created_at"

    def wallet_user(self, obj):
        """Display wallet user with link"""
        if obj.wallet and obj.wallet.user:
            url = reverse("admin:authentication_tainouser_change", args=[obj.wallet.user.id])
            return format_html(
                '<a href="{}" style="text-decoration: none;">{}</a><br/><small style="color: #666;">{}</small>',
                url,
                obj.wallet.user.get_full_name() or "بدون نام",
                obj.wallet.user.email or obj.wallet.user.phone_number or "-",
            )
        return "-"

    wallet_user.short_description = _("کاربر")

    def amount_display(self, obj):
        """Display amount with color coding"""
        if not obj.amount or obj.amount == 0:
            return format_html('<span style="color: #999;">-</span>')

        formatted_amount = f"{int(abs(obj.amount)):,}"
        color = "#4caf50" if obj.type in ["deposit", "refund", "coin_refund", "coin_reward"] else "#f44336"
        sign = "+" if obj.type in ["deposit", "refund", "coin_refund", "coin_reward"] else "-"

        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 14px;">{}{}</span>',
            color,
            sign,
            formatted_amount,
        )

    amount_display.short_description = _("مبلغ")

    def coin_amount_display(self, obj):
        """Display coin amount with color coding"""
        if not obj.coin_amount or obj.coin_amount == 0:
            return format_html('<span style="color: #999;">-</span>')

        formatted_coin_amount = f"{int(abs(obj.coin_amount)):,}"
        color = "#ff9800" if obj.type in ["coin_purchase", "coin_refund", "coin_reward"] else "#9c27b0"
        sign = "+" if obj.type in ["coin_purchase", "coin_refund", "coin_reward"] else "-"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{}</span> <small>سکه</small>',
            color,
            sign,
            formatted_coin_amount,
        )

    coin_amount_display.short_description = _("تعداد سکه")

    def type_badge(self, obj):
        """Display transaction type as badge"""
        type_colors = {
            "deposit": "#4caf50",
            "withdrawal": "#f44336",
            "payment": "#ff9800",
            "refund": "#2196f3",
            "consultation_fee": "#9c27b0",
            "coin_purchase": "#ff9800",
            "coin_usage": "#9c27b0",
            "coin_refund": "#00bcd4",
            "coin_reward": "#ffeb3b",
            "ai_chat": "#673ab7",
            "sms_buying": "#3f51b5",
            "sms_usage": "#009688",
        }
        color = type_colors.get(obj.type, "#666")
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; '
            'border-radius: 3px; font-size: 11px; white-space: nowrap;">{}</span>',
            color,
            obj.get_type_display(),
        )

    type_badge.short_description = _("نوع تراکنش")

    def status_badge(self, obj):
        """Display transaction status as badge"""
        status_config = {
            "pending": ("#ff9800", "⏳"),
            "completed": ("#4caf50", "✓"),
            "failed": ("#f44336", "✗"),
            "canceled": ("#666", "⊘"),
        }
        color, icon = status_config.get(obj.status, ("#666", "?"))
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; '
            'border-radius: 3px; font-size: 11px;">{} {}</span>',
            color,
            icon,
            obj.get_status_display(),
        )

    status_badge.short_description = _("وضعیت")

    def user_statistics(self, obj):
        """نمایش آمار تراکنش‌های این کاربر"""
        from django.db.models import Count, Sum

        if not obj.wallet:
            return "-"

        # فقط تراکنش‌های کیف پول این کاربر
        user_transactions = Transaction.objects.filter(wallet=obj.wallet)

        # تعداد تراکنش‌ها بر اساس نوع
        type_stats = user_transactions.values("type").annotate(count=Count("type")).order_by("-count")

        # تعداد تراکنش‌ها بر اساس وضعیت
        status_stats = user_transactions.values("status").annotate(count=Count("status"))

        # محاسبه آمار مالی
        completed_transactions = user_transactions.filter(status="completed")
        total_deposits = (
            completed_transactions.filter(type__in=["deposit", "refund"]).aggregate(total=Sum("amount"))["total"] or 0
        )
        total_withdrawals = (
            completed_transactions.filter(type__in=["withdrawal", "payment"]).aggregate(total=Sum("amount"))["total"] or 0
        )
        total_coins_purchased = (
            completed_transactions.filter(type__in=["coin_purchase", "coin_reward"]).aggregate(total=Sum("coin_amount"))[
                "total"
            ]
            or 0
        )
        total_coins_used = completed_transactions.filter(type="coin_usage").aggregate(total=Sum("coin_amount"))["total"] or 0

        total_transactions = user_transactions.count()

        html = '<div style="background: #f5f5f5; padding: 20px; border-radius: 8px;">'

        # هدر با اطلاعات کاربر
        user = obj.wallet.user
        html += f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 8px; color: white; margin-bottom: 20px;">
            <h2 style="margin: 0 0 10px 0;">👤 آمار تراکنش‌های {user.get_full_name() or "کاربر"}</h2>
            <p style="margin: 0; opacity: 0.9; font-size: 14px;">
                {user.email or user.phone_number or "-"}
            </p>
        </div>
        """

        # کارت‌های آمار سریع
        html += '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px;">'

        cards = [
            ("🔢", "کل تراکنش‌ها", total_transactions, "#2196f3"),
            ("✅", "تراکنش موفق", completed_transactions.count(), "#4caf50"),
            ("💰", "کل واریزی", f"{int(total_deposits):,}", "#00bcd4"),
            ("🪙", "سکه خریداری", f"{int(total_coins_purchased):,}", "#ff9800"),
        ]

        for icon, label, value, color in cards:
            html += f"""
            <div style="background: white; padding: 15px; border-radius: 8px; 
                        border-top: 3px solid {color}; text-align: center;">
                <div style="font-size: 24px; margin-bottom: 5px;">{icon}</div>
                <div style="font-size: 20px; font-weight: bold; color: {color}; margin-bottom: 5px;">
                    {value}
                </div>
                <div style="color: #666; font-size: 12px;">{label}</div>
            </div>
            """

        html += "</div>"

        # نمودار توزیع انواع تراکنش
        html += '<div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">'
        html += '<h3 style="color: #333; margin: 0 0 15px 0;">📊 توزیع انواع تراکنش</h3>'

        type_colors = {
            "deposit": "#4caf50",
            "withdrawal": "#f44336",
            "payment": "#ff9800",
            "coin_purchase": "#ff9800",
            "coin_usage": "#9c27b0",
            "refund": "#2196f3",
        }

        for stat in type_stats[:6]:
            transaction_type = dict(Transaction.TRANSACTION_TYPES).get(stat["type"], stat["type"])
            count = stat["count"]
            percentage = (count / total_transactions * 100) if total_transactions > 0 else 0
            bar_color = type_colors.get(stat["type"], "#2196f3")

            html += f"""
            <div style="margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="font-weight: 500; color: #555;">{transaction_type}</span>
                    <span style="color: #666; font-size: 14px;">{count} ({percentage:.1f}%)</span>
                </div>
                <div style="background: #e0e0e0; border-radius: 10px; height: 24px; overflow: hidden;">
                    <div style="background: {bar_color}; height: 100%; width: {percentage}%; 
                                transition: width 0.3s; border-radius: 10px;"></div>
                </div>
            </div>
            """

        html += "</div>"

        # وضعیت تراکنش‌ها
        html += '<div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">'
        html += '<h3 style="color: #333; margin: 0 0 15px 0;">📈 وضعیت تراکنش‌ها</h3>'
        html += '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;">'

        status_colors = {
            "completed": "#4caf50",
            "pending": "#ff9800",
            "failed": "#f44336",
            "canceled": "#666",
        }

        for stat in status_stats:
            status_name = dict(Transaction.TRANSACTION_STATUS).get(stat["status"], stat["status"])
            count = stat["count"]
            percentage = (count / total_transactions * 100) if total_transactions > 0 else 0
            color = status_colors.get(stat["status"], "#2196f3")

            html += f"""
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; 
                        border-right: 4px solid {color}; text-align: center;">
                <div style="font-size: 28px; font-weight: bold; color: {color}; margin-bottom: 5px;">
                    {count}
                </div>
                <div style="color: #666; font-size: 13px; margin-bottom: 3px;">{status_name}</div>
                <div style="color: #999; font-size: 11px;">{percentage:.1f}%</div>
            </div>
            """

        html += "</div></div>"

        # خلاصه مالی
        html += '<div style="background: white; padding: 20px; border-radius: 8px;">'
        html += '<h3 style="color: #333; margin: 0 0 15px 0;">💳 خلاصه مالی</h3>'
        html += '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">'

        financial_items = [
            ("💵", "مجموع واریزی", f"{int(total_deposits):,}", "#4caf50"),
            ("💸", "مجموع برداشت", f"{int(abs(total_withdrawals)):,}", "#f44336"),
            ("🪙", "سکه خریداری", f"{int(total_coins_purchased):,}", "#ff9800"),
            ("⚡", "سکه مصرف شده", f"{int(abs(total_coins_used)):,}", "#9c27b0"),
        ]

        for icon, label, value, color in financial_items:
            html += f"""
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; 
                        display: flex; align-items: center; gap: 15px;">
                <div style="font-size: 32px;">{icon}</div>
                <div style="flex: 1;">
                    <div style="color: #666; font-size: 12px; margin-bottom: 3px;">{label}</div>
                    <div style="font-size: 18px; font-weight: bold; color: {color};">{value}</div>
                </div>
            </div>
            """

        html += "</div></div>"
        html += "</div>"

        return format_html(html)

    user_statistics.short_description = _("آمار کاربر")

    def all_transactions_statistics(self, obj):
        """نمایش آمار کل تراکنش‌های سیستم"""
        from django.db.models import Count, Sum

        # تمام تراکنش‌های سیستم
        all_transactions = Transaction.objects.all()

        # تعداد تراکنش‌ها بر اساس نوع
        type_stats = all_transactions.values("type").annotate(count=Count("type")).order_by("-count")

        # تعداد تراکنش‌ها بر اساس وضعیت
        status_stats = all_transactions.values("status").annotate(count=Count("status"))

        # آمار مالی کل
        completed_all = all_transactions.filter(status="completed")
        total_amount = completed_all.aggregate(total=Sum("amount"))["total"] or 0
        total_coins = completed_all.aggregate(total=Sum("coin_amount"))["total"] or 0

        total_count = all_transactions.count()
        unique_users = all_transactions.values("wallet__user").distinct().count()

        html = '<div style="background: #f5f5f5; padding: 20px; border-radius: 8px;">'

        # هدر
        html += """
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    padding: 20px; border-radius: 8px; color: white; margin-bottom: 20px;">
            <h2 style="margin: 0 0 10px 0;">🌍 آمار کل تراکنش‌های سیستم</h2>
            <p style="margin: 0; opacity: 0.9; font-size: 14px;">
                نمای کلی از تمام تراکنش‌ها در سیستم
            </p>
        </div>
        """

        # کارت‌های آمار کلی
        html += '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px;">'

        cards = [
            ("📊", "کل تراکنش‌ها", f"{total_count:,}", "#2196f3"),
            ("👥", "کاربران فعال", unique_users, "#9c27b0"),
            ("✅", "تراکنش موفق", completed_all.count(), "#4caf50"),
            ("💰", "گردش مالی", f"{int(abs(total_amount)):,}", "#ff9800"),
        ]

        for icon, label, value, color in cards:
            html += f"""
            <div style="background: white; padding: 15px; border-radius: 8px; 
                        border-top: 3px solid {color}; text-align: center;">
                <div style="font-size: 24px; margin-bottom: 5px;">{icon}</div>
                <div style="font-size: 20px; font-weight: bold; color: {color}; margin-bottom: 5px;">
                    {value}
                </div>
                <div style="color: #666; font-size: 12px;">{label}</div>
            </div>
            """

        html += "</div>"

        # نمودار توزیع انواع تراکنش
        html += '<div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">'
        html += '<h3 style="color: #333; margin: 0 0 15px 0;">📊 توزیع کل انواع تراکنش</h3>'

        type_colors = {
            "deposit": "#4caf50",
            "withdrawal": "#f44336",
            "payment": "#ff9800",
            "coin_purchase": "#ff9800",
            "coin_usage": "#9c27b0",
            "refund": "#2196f3",
        }

        for stat in type_stats:
            transaction_type = dict(Transaction.TRANSACTION_TYPES).get(stat["type"], stat["type"])
            count = stat["count"]
            percentage = (count / total_count * 100) if total_count > 0 else 0
            bar_color = type_colors.get(stat["type"], "#2196f3")

            html += f"""
            <div style="margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="font-weight: 500; color: #555;">{transaction_type}</span>
                    <span style="color: #666; font-size: 14px;">{count:,} ({percentage:.1f}%)</span>
                </div>
                <div style="background: #e0e0e0; border-radius: 10px; height: 24px; overflow: hidden;">
                    <div style="background: {bar_color}; height: 100%; width: {percentage}%; 
                                transition: width 0.3s; border-radius: 10px;"></div>
                </div>
            </div>
            """

        html += "</div>"

        # وضعیت تراکنش‌ها
        html += '<div style="background: white; padding: 20px; border-radius: 8px;">'
        html += '<h3 style="color: #333; margin: 0 0 15px 0;">📈 وضعیت کل تراکنش‌ها</h3>'
        html += '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;">'

        status_colors = {
            "completed": "#4caf50",
            "pending": "#ff9800",
            "failed": "#f44336",
            "canceled": "#666",
        }

        for stat in status_stats:
            status_name = dict(Transaction.TRANSACTION_STATUS).get(stat["status"], stat["status"])
            count = stat["count"]
            percentage = (count / total_count * 100) if total_count > 0 else 0
            color = status_colors.get(stat["status"], "#2196f3")

            html += f"""
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; 
                        border-right: 4px solid {color}; text-align: center;">
                <div style="font-size: 28px; font-weight: bold; color: {color}; margin-bottom: 5px;">
                    {count:,}
                </div>
                <div style="color: #666; font-size: 13px; margin-bottom: 3px;">{status_name}</div>
                <div style="color: #999; font-size: 11px;">{percentage:.1f}%</div>
            </div>
            """

        html += "</div></div>"
        html += "</div>"

        return format_html(html)

    all_transactions_statistics.short_description = _("آمار کل سیستم")

    def metadata_display(self, obj):
        """Display metadata in a formatted way"""
        if not obj.metadata:
            return "-"

        import json

        try:
            formatted = json.dumps(obj.metadata, indent=2, ensure_ascii=False)
            return format_html(
                '<pre style="background: #f5f5f5; padding: 10px; border-radius: 5px; '
                'font-size: 12px; max-width: 600px; overflow-x: auto;">{}</pre>',
                formatted,
            )
        except Exception:
            return str(obj.metadata)

    metadata_display.short_description = _("متادیتا")

    def has_add_permission(self, request):
        """Prevent manual transaction creation"""
        return True

    def has_change_permission(self, request, obj=None):
        """Prevent transaction editing"""
        return False


@admin.register(CoinSettings)
class CoinSettingsAdmin(admin.ModelAdmin):
    """Admin interface for CoinSettings model"""

    list_display = [
        "exchange_rate_display",
        "is_default_badge",
        "is_active_badge",
        "description_short",
        "created_at",
        "actions_column",
    ]
    list_filter = ["is_active", "is_default", "created_at"]
    search_fields = ["description"]
    readonly_fields = ["pid", "created_at", "updated_at", "ctainoersion_examples"]
    fieldsets = (
        (
            _("تنظیمات نرخ تبدیل"),
            {
                "fields": ("exchange_rate", "description"),
            },
        ),
        (
            _("وضعیت"),
            {
                "fields": ("is_active", "is_default"),
            },
        ),
        (
            _("مثال‌های تبدیل"),
            {
                "fields": ("ctainoersion_examples",),
                "classes": ("collapse",),
            },
        ),
        (
            _("اطلاعات سیستم"),
            {
                "fields": ("pid", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def exchange_rate_display(self, obj):
        """Display exchange rate with formatting"""
        # FIX: Format numbers before passing to format_html
        formatted_rate = f"{int(obj.exchange_rate):,}"
        return format_html(
            '<span style="font-size: 16px; font-weight: bold; color: #2196f3;">{}</span> '
            '<small style="color: #666;">ریال = 1 سکه</small>',
            formatted_rate,
        )

    exchange_rate_display.short_description = _("نرخ تبدیل")

    def is_default_badge(self, obj):
        """Display default status as badge"""
        if obj.is_default:
            return format_html(
                '<span style="background: #4caf50; color: white; padding: 4px 8px; '
                'border-radius: 3px; font-size: 11px;">✓ پیش فرض</span>'
            )
        return format_html('<span style="color: #999;">-</span>')

    is_default_badge.short_description = _("پیش فرض")

    def is_active_badge(self, obj):
        """Display active status as badge"""
        if obj.is_active:
            return format_html(
                '<span style="background: #4caf50; color: white; padding: 4px 8px; '
                'border-radius: 3px; font-size: 11px;">✓ فعال</span>'
            )
        return format_html(
            '<span style="background: #f44336; color: white; padding: 4px 8px; '
            'border-radius: 3px; font-size: 11px;">✗ غیرفعال</span>'
        )

    is_active_badge.short_description = _("وضعیت")

    def description_short(self, obj):
        """Display short description"""
        if obj.description:
            return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
        return "-"

    description_short.short_description = _("توضیحات")

    def ctainoersion_examples(self, obj):
        """Display ctainoersion examples"""
        examples = [
            (10000, CoinSettings.ctainoert_rial_to_coin(10000)),
            (50000, CoinSettings.ctainoert_rial_to_coin(50000)),
            (100000, CoinSettings.ctainoert_rial_to_coin(100000)),
            (500000, CoinSettings.ctainoert_rial_to_coin(500000)),
            (1000000, CoinSettings.ctainoert_rial_to_coin(1000000)),
        ]

        html = '<div style="background: #f5f5f5; padding: 15px; border-radius: 5px;">'
        html += "<strong>مثال‌های تبدیل:</strong><br/><br/>"

        for rial, coin in examples:
            # FIX: Format numbers before adding to HTML
            formatted_rial = f"{rial:,}"
            formatted_coin = f"{coin:,}"
            html += f'<div style="margin-bottom: 8px;">'
            html += f'<span style="color: #4caf50; font-weight: bold;">{formatted_rial} ریال</span> = '
            html += f'<span style="color: #ff9800; font-weight: bold;">{formatted_coin} سکه</span>'
            html += f"</div>"

        html += "</div>"
        return format_html(html)

    ctainoersion_examples.short_description = _("مثال‌های تبدیل")

    def actions_column(self, obj):
        """Display action buttons"""
        html = ""
        if not obj.is_default:
            html += format_html(
                '<a href="#" onclick="return confirm(\'آیا مطمئن هستید؟\');" '
                'style="background: #4caf50; color: white; padding: 5px 10px; '
                'border-radius: 3px; text-decoration: none; font-size: 12px; margin-left: 5px;">'
                "تنظیم به عنوان پیش فرض</a>"
            )
        return format_html(html) if html else "-"

    actions_column.short_description = _("عملیات")


@admin.register(CoinPackage)
class CoinPackageAdmin(admin.ModelAdmin):
    """Admin interface for CoinPackage model"""

    list_display = [
        "label_display",
        "value_display",
        "price_display",
        "price_per_coin_display",
        "role_badge",
        "order",
        "is_active_badge",
        "created_at",
    ]
    list_filter = ["is_active", "role", "created_at"]
    search_fields = ["label", "description", "pid"]
    readonly_fields = ["pid", "price_per_coin_display", "created_at", "updated_at"]
    fieldsets = (
        (
            _("اطلاعات پکیج"),
            {
                "fields": ("label", "value", "price", "description"),
            },
        ),
        (
            _("دسته‌بندی"),
            {
                "fields": ("role", "order"),
            },
        ),
        (
            _("وضعیت"),
            {
                "fields": ("is_active",),
            },
        ),
        (
            _("محاسبات"),
            {
                "fields": ("price_per_coin_display",),
                "classes": ("collapse",),
            },
        ),
        (
            _("اطلاعات سیستم"),
            {
                "fields": ("pid", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
    ordering = ["order", "value"]

    def label_display(self, obj):
        """Display label with icon"""
        return format_html(
            '<span style="font-weight: bold; font-size: 14px;">🎁 {}</span>',
            obj.label,
        )

    label_display.short_description = _("عنوان پکیج")

    def value_display(self, obj):
        """Display coin value with formatting"""
        # FIX: Format numbers before passing to format_html
        formatted_value = f"{obj.value:,}"
        return format_html(
            '<span style="color: #ff9800; font-weight: bold; font-size: 14px;">{}</span> '
            '<small style="color: #666;">سکه</small>',
            formatted_value,
        )

    value_display.short_description = _("تعداد سکه")

    def price_display(self, obj):
        """Display price with formatting"""
        # FIX: Format numbers before passing to format_html
        formatted_price = f"{int(obj.price):,}"
        return format_html(
            '<span style="color: #4caf50; font-weight: bold; font-size: 14px;">{}</span> '
            '<small style="color: #666;">ریال</small>',
            formatted_price,
        )

    price_display.short_description = _("قیمت")

    def price_per_coin_display(self, obj):
        """Display price per coin"""
        if obj.price_per_coin:
            # FIX: Format numbers before passing to format_html
            formatted_price_per_coin = f"{obj.price_per_coin:,.0f}"
            return format_html(
                '<span style="color: #2196f3; font-weight: bold;">{}</span> '
                '<small style="color: #666;">ریال به ازای هر سکه</small>',
                formatted_price_per_coin,
            )
        return "-"

    price_per_coin_display.short_description = _("قیمت هر سکه")

    def role_badge(self, obj):
        """Display role as badge"""
        if obj.role:
            return format_html(
                '<span style="background: #673ab7; color: white; padding: 4px 8px; '
                'border-radius: 3px; font-size: 11px;">{}</span>',
                obj.role.name,
            )
        return format_html(
            '<span style="background: #00bcd4; color: white; padding: 4px 8px; '
            'border-radius: 3px; font-size: 11px;">عمومی</span>'
        )

    role_badge.short_description = _("نقش کاربری")

    def is_active_badge(self, obj):
        """Display active status as badge"""
        if obj.is_active:
            return format_html(
                '<span style="background: #4caf50; color: white; padding: 4px 8px; '
                'border-radius: 3px; font-size: 11px;">✓ فعال</span>'
            )
        return format_html(
            '<span style="background: #f44336; color: white; padding: 4px 8px; '
            'border-radius: 3px; font-size: 11px;">✗ غیرفعال</span>'
        )

    is_active_badge.short_description = _("وضعیت")
