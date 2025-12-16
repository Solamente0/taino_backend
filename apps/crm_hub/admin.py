"""
apps/crm_hub/admin.py
Django admin configuration for CRM Hub
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from import_export.admin import ImportExportModelAdmin

from apps.crm_hub.models import CRMCampaign, CRMUserEngagement, CRMNotificationLog


@admin.register(CRMCampaign)
class CRMCampaignAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [
        "name",
        "static_name",
        "campaign_type",
        "trigger_days",
        "channels_display",
        "is_active",
        "priority",
        "created_at",
    ]

    list_filter = [
        "campaign_type",
        "is_active",
        "require_no_activity",
        "require_no_subscription",
        "created_at",
    ]

    search_fields = [
        "name",
        "static_name",
        "description",
    ]

    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("اطلاعات پایه", {"fields": ("name", "static_name", "description", "campaign_type", "is_active", "priority")}),
        ("تنظیمات اجرا", {"fields": ("trigger_days", "channels", "max_sends_per_user", "target_user_roles")}),
        ("شرایط هدف‌گیری", {"fields": ("require_no_activity", "require_no_subscription", "subscription_expire_threshold")}),
        ("محتوای ایمیل", {"fields": ("email_subject", "email_template"), "classes": ("collapse",)}),
        ("محتوای پیامک", {"fields": ("sms_template",), "classes": ("collapse",)}),
        ("محتوای اعلان", {"fields": ("push_title", "push_body"), "classes": ("collapse",)}),
        ("تاریخ‌ها", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def channels_display(self, obj):
        """Display channels as badges"""
        if not obj.channels:
            return "-"

        badges = []
        for channel in obj.channels:
            badges.append(f'<span class="badge badge-info" style="margin: 2px;">{channel}</span>')
        return mark_safe(" ".join(badges))

    channels_display.short_description = "کانال‌های ارسال"

    actions = ["activate_campaigns", "deactivate_campaigns", "test_campaign"]

    def activate_campaigns(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} کمپین فعال شد")

    activate_campaigns.short_description = "فعال‌سازی کمپین‌های انتخاب شده"

    def deactivate_campaigns(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} کمپین غیرفعال شد")

    deactivate_campaigns.short_description = "غیرفعال‌سازی کمپین‌های انتخاب شده"


@admin.register(CRMUserEngagement)
class CRMUserEngagementAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [
        "user_link",
        "engagement_score_display",
        "churn_risk_display",
        "last_activity_date",
        "activities_last_7_days",
        "has_active_subscription",
        "subscription_days_remaining",
    ]

    list_filter = [
        "has_active_subscription",
        "last_activity_date",
    ]

    search_fields = [
        "user__phone_number",
        "user__email",
        "user__first_name",
        "user__last_name",
    ]

    readonly_fields = [
        "user",
        "last_login_date",
        "last_activity_date",
        "total_activities",
        "activities_last_7_days",
        "activities_last_30_days",
        "has_active_subscription",
        "subscription_expire_date",
        "subscription_days_remaining",
        "subscription_usage_percent",
        "engagement_score",
        "churn_risk_score",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        ("کاربر", {"fields": ("user",)}),
        (
            "فعالیت",
            {
                "fields": (
                    "last_login_date",
                    "last_activity_date",
                    "total_activities",
                    "activities_last_7_days",
                    "activities_last_30_days",
                )
            },
        ),
        (
            "اشتراک",
            {
                "fields": (
                    "has_active_subscription",
                    "subscription_expire_date",
                    "subscription_days_remaining",
                    "subscription_usage_percent",
                )
            },
        ),
        ("امتیازها", {"fields": ("engagement_score", "churn_risk_score")}),
        ("تاریخ‌ها", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def user_link(self, obj):
        """Link to user admin page"""
        url = reverse("admin:authentication_tainouser_change", args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())

    user_link.short_description = "کاربر"

    def engagement_score_display(self, obj):
        """Display engagement score with color"""
        score = obj.engagement_score
        if score >= 70:
            color = "green"
        elif score >= 40:
            color = "orange"
        else:
            color = "red"
        return format_html('<span style="color: {}; font-weight: bold;">{:.1f}</span>', color, score)

    engagement_score_display.short_description = "امتیاز تعامل"

    def churn_risk_display(self, obj):
        """Display churn risk with color"""
        risk = obj.churn_risk_score
        if risk >= 70:
            color = "red"
        elif risk >= 40:
            color = "orange"
        else:
            color = "green"
        return format_html('<span style="color: {}; font-weight: bold;">{:.1f}</span>', color, risk)

    churn_risk_display.short_description = "خطر ترک"

    actions = ["update_engagement"]

    def update_engagement(self, request, queryset):
        """Update engagement metrics for selected users"""
        from apps.crm_hub.services.engagement import EngagementTrackingService

        count = 0
        for engagement in queryset:
            try:
                EngagementTrackingService.update_user_engagement(engagement.user)
                count += 1
            except Exception as e:
                self.message_user(request, f"خطا در به‌روزرسانی {engagement.user}: {e}", level="error")

        self.message_user(request, f"{count} کاربر به‌روزرسانی شد")

    update_engagement.short_description = "به‌روزرسانی امتیاز تعامل"


@admin.register(CRMNotificationLog)
class CRMNotificationLogAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ["user_link", "campaign_link", "channel", "status_display", "sent_at", "created_at"]

    list_filter = [
        "channel",
        "status",
        "campaign",
        "sent_at",
        "created_at",
    ]

    search_fields = [
        "user__phone_number",
        "user__email",
        "user__first_name",
        "user__last_name",
        "subject",
        "content",
    ]

    readonly_fields = [
        "user",
        "campaign",
        "channel",
        "status",
        "subject",
        "content",
        "sent_at",
        "delivered_at",
        "opened_at",
        "error_message",
        "metadata",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        ("اطلاعات پایه", {"fields": ("user", "campaign", "channel", "status")}),
        ("محتوا", {"fields": ("subject", "content")}),
        ("زمان‌بندی", {"fields": ("sent_at", "delivered_at", "opened_at")}),
        ("خطا", {"fields": ("error_message",), "classes": ("collapse",)}),
        ("اطلاعات اضافی", {"fields": ("metadata",), "classes": ("collapse",)}),
        ("تاریخ‌ها", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def has_add_permission(self, request):
        """Disable adding logs through admin"""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable editing logs through admin"""
        return False

    def user_link(self, obj):
        """Link to user admin page"""
        url = reverse("admin:authentication_tainouser_change", args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())

    user_link.short_description = "کاربر"

    def campaign_link(self, obj):
        """Link to campaign admin page"""
        if obj.campaign:
            url = reverse("admin:crm_hub_crmcampaign_change", args=[obj.campaign.pk])
            return format_html('<a href="{}">{}</a>', url, obj.campaign.name)
        return "-"

    campaign_link.short_description = "کمپین"

    def status_display(self, obj):
        """Display status with color"""
        colors = {
            "pending": "#6c757d",
            "sent": "#007bff",
            "failed": "#dc3545",
            "delivered": "#28a745",
            "opened": "#17a2b8",
            "clicked": "#ffc107",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_status_display())

    status_display.short_description = "وضعیت"
