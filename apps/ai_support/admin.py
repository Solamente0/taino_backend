# apps/ai_support/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from import_export.admin import ImportExportModelAdmin

from apps.ai_support.models import SupportSession, SupportMessage, SupportAIConfig


class SupportMessageInline(admin.TabularInline):
    """Inline for viewing messages"""

    model = SupportMessage
    extra = 0
    can_delete = False
    fields = ["created_at", "sender_name", "message_preview", "is_ai", "is_read"]
    readonly_fields = ["created_at", "sender_name", "message_preview", "is_ai", "is_read"]
    ordering = ["-created_at"]

    def sender_name(self, obj):
        return f"{obj.sender.first_name} {obj.sender.last_name}"

    sender_name.short_description = "فرستنده"

    def message_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content

    message_preview.short_description = "پیش‌نمایش"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(SupportSession)
class SupportSessionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ["colored_pid", "user_link", "status_badge", "message_count", "created_time"]
    list_filter = ["status", "created_at"]
    search_fields = ["pid", "user__email", "user__first_name", "user__last_name", "subject"]
    readonly_fields = ["pid", "created_at", "updated_at"]

    fieldsets = (
        ("اطلاعات اصلی", {"fields": ("pid", "user", "subject", "status")}),
        ("پیام‌ها", {"fields": ("total_messages", "unread_messages")}),
        ("تاریخچه", {"fields": ("created_at", "updated_at")}),
    )

    inlines = [SupportMessageInline]

    def colored_pid(self, obj):
        colors = {"active": "#28a745", "closed": "#dc3545"}
        color = colors.get(obj.status, "#007bff")
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.pid)

    colored_pid.short_description = "شناسه"

    def user_link(self, obj):
        url = reverse("admin:authentication_tainouser_change", args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())

    user_link.short_description = "کاربر"

    def status_badge(self, obj):
        badges = {
            "active": ("success", "✓ فعال"),
            "closed": ("secondary", "✗ بسته شده"),
        }
        badge_class, label = badges.get(obj.status, ("info", obj.status))
        return format_html('<span class="badge badge-{}">{}</span>', badge_class, label)

    status_badge.short_description = "وضعیت"

    def message_count(self, obj):
        unread = obj.unread_messages
        total = obj.total_messages

        if unread > 0:
            return format_html(
                "<strong>{}</strong> / {} <span class='badge badge-danger'>{} خوانده نشده</span>", total, total, unread
            )
        return format_html("<strong>{}</strong>", total)

    message_count.short_description = "تعداد پیام"

    def created_time(self, obj):
        return format_html(
            '<div style="direction: ltr; text-align: left;">{}</div>', obj.created_at.strftime("%Y-%m-%d %H:%M")
        )

    created_time.short_description = "زمان ایجاد"


@admin.register(SupportMessage)
class SupportMessageAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [
        "colored_pid",
        "session_link",
        "sender_info",
        "message_preview",
        "ai_badge",
        "read_status",
        "created_time",
    ]
    list_filter = ["is_ai", "is_read", "created_at"]
    search_fields = ["pid", "content", "sender__email", "session__pid"]
    readonly_fields = ["pid", "created_at", "updated_at", "full_content"]

    fieldsets = (
        ("اطلاعات اصلی", {"fields": ("pid", "session", "sender", "message_type")}),
        ("محتوا", {"fields": ("full_content", "attachment")}),
        ("وضعیت", {"fields": ("is_ai", "is_read", "read_at")}),
        ("تاریخچه", {"fields": ("created_at", "updated_at")}),
    )

    def colored_pid(self, obj):
        color = "#007bff" if obj.is_ai else "#28a745"
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.pid)

    colored_pid.short_description = "شناسه"

    def session_link(self, obj):
        url = reverse("admin:ai_support_supportsession_change", args=[obj.session.pk])
        return format_html('<a href="{}">جلسه {}</a>', url, obj.session.pid)

    session_link.short_description = "جلسه"

    def sender_info(self, obj):
        return format_html(
            "<div><strong>{}</strong><br><small>{}</small></div>", obj.sender.get_full_name(), obj.sender.email
        )

    sender_info.short_description = "فرستنده"

    def message_preview(self, obj):
        preview = obj.content[:60] + "..." if len(obj.content) > 60 else obj.content
        return format_html('<div style="max-width: 300px; overflow: hidden;" title="{}">{}</div>', obj.content, preview)

    message_preview.short_description = "پیش‌نمایش"

    def ai_badge(self, obj):
        if obj.is_ai:
            return format_html('<span class="badge badge-info">🤖 AI</span>')
        return format_html('<span class="badge badge-success">👤 کاربر</span>')

    ai_badge.short_description = "نوع"

    def read_status(self, obj):
        if obj.is_read:
            return format_html('<span class="badge badge-success">✓ خوانده شده</span>')
        return format_html('<span class="badge badge-secondary">خوانده نشده</span>')

    read_status.short_description = "وضعیت خواندن"

    def created_time(self, obj):
        return format_html(
            '<div style="direction: ltr; text-align: left;">{}</div>', obj.created_at.strftime("%Y-%m-%d %H:%M")
        )

    created_time.short_description = "زمان"

    def full_content(self, obj):
        return format_html(
            '<div style="max-width: 600px; padding: 10px; background: #f8f9fa; border-radius: 5px; white-space: pre-wrap;">{}</div>',
            obj.content,
        )

    full_content.short_description = "محتوای کامل"


@admin.register(SupportAIConfig)
class SupportAIConfigAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ["colored_name", "model_badge", "status_badge", "usage_stats", "default_badge", "last_used_time"]
    list_filter = ["is_default", "is_active", "created_at"]
    search_fields = ["name", "model_name", "api_key"]
    readonly_fields = ["pid", "created_at", "updated_at", "total_requests", "total_errors", "last_used_at", "usage_chart"]

    fieldsets = (
        ("📋 اطلاعات اصلی", {"fields": ("pid", "name", "creator", "is_default")}),
        ("🔑 تنظیمات OpenRouter", {"fields": ("api_key", "base_url", "model_name")}),
        ("📝 دستورالعمل سیستمی", {"fields": ("system_prompt", "fallback_message")}),
        (
            "⚙️ پارامترهای مدل",
            {
                "fields": ("temperature", "max_tokens", "ctainoersation_history_limit", "response_delay_seconds"),
                "classes": ("collapse",),
            },
        ),
        (
            "📊 آمار استفاده",
            {"fields": ("total_requests", "total_errors", "last_used_at", "usage_chart"), "classes": ("collapse",)},
        ),
        ("📅 تاریخچه", {"fields": ("is_active", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    actions = ["mark_as_default", "test_configuration"]

    def colored_name(self, obj):
        color = "#28a745" if obj.is_default else "#007bff"
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.name)

    colored_name.short_description = "نام"

    def model_badge(self, obj):
        # Show model name in a badge
        model_parts = obj.model_name.split("/")
        model_display = model_parts[-1] if len(model_parts) > 1 else obj.model_name

        # Check if it's a free model
        is_free = ":free" in obj.model_name
        badge_class = "success" if is_free else "info"

        return format_html('<span class="badge badge-{}">{} {}</span>', badge_class, model_display, "🆓" if is_free else "")

    model_badge.short_description = "مدل"

    def status_badge(self, obj):
        if obj.is_active:
            return format_html('<span class="badge badge-success">✓ فعال</span>')
        return format_html('<span class="badge badge-danger">✗ غیرفعال</span>')

    status_badge.short_description = "وضعیت"

    def usage_stats(self, obj):
        success_rate = 0
        if obj.total_requests > 0:
            success_rate = ((obj.total_requests - obj.total_errors) / obj.total_requests) * 100

        # Format the success rate as string before passing to format_html
        success_rate_formatted = f"{success_rate:.1f}"

        return format_html(
            "<div>" "<strong>{}</strong> درخواست<br>" '<small style="color: {};">{} خطا ({}% موفق)</small>' "</div>",
            obj.total_requests,
            "#dc3545" if obj.total_errors > 0 else "#28a745",
            obj.total_errors,
            success_rate_formatted,  # Use pre-formatted string
        )

    usage_stats.short_description = "آمار استفاده"

    def default_badge(self, obj):
        if obj.is_default:
            return format_html('<span class="badge badge-warning">⭐ پیش‌فرض</span>')
        return "-"

    default_badge.short_description = "پیش‌فرض"

    def last_used_time(self, obj):
        if obj.last_used_at:
            return format_html(
                '<div style="direction: ltr; text-align: left;">{}</div>', obj.last_used_at.strftime("%Y-%m-%d %H:%M")
            )
        return format_html('<span style="color: #6c757d;">هرگز</span>')

    last_used_time.short_description = "آخرین استفاده"

    def usage_chart(self, obj):
        """Visual chart for usage statistics"""
        if obj.total_requests == 0:
            return format_html('<div class="alert alert-info">هنوز استفاده نشده</div>')

        success_count = obj.total_requests - obj.total_errors
        success_pct = (success_count / obj.total_requests) * 100
        error_pct = 100 - success_pct

        # Pre-format the percentage values
        success_pct_formatted = f"{success_pct:.0f}"
        error_pct_formatted = f"{error_pct:.0f}"

        return format_html(
            '<div style="width: 100%; background: #f0f0f0; border-radius: 5px; overflow: hidden;">'
            '<div style="display: flex; height: 30px;">'
            '<div style="width: {}%; background: #28a745; display: flex; align-items: center; justify-content: center; color: white; font-size: 11px;">'
            "✓ {} ({}%)"
            "</div>"
            '<div style="width: {}%; background: #dc3545; display: flex; align-items: center; justify-content: center; color: white; font-size: 11px;">'
            "✗ {} ({}%)"
            "</div>"
            "</div>"
            "</div>"
            '<div style="margin-top: 10px;">'
            "<strong>مجموع:</strong> {} درخواست"
            "</div>",
            success_pct,
            success_count,
            success_pct_formatted,  # Use pre-formatted percentage
            error_pct,
            obj.total_errors,
            error_pct_formatted,  # Use pre-formatted percentage
            obj.total_requests,
        )

    usage_chart.short_description = "نمودار استفاده"

    # Actions
    def mark_as_default(self, request, queryset):
        """Mark selected config as default"""
        if queryset.count() > 1:
            self.message_user(request, "فقط می‌توانید یک پیکربندی را به عنوان پیش‌فرض انتخاب کنید.", level="error")
            return

        # Unset all defaults
        SupportAIConfig.objects.filter(is_default=True).update(is_default=False)

        # Set new default
        config = queryset.first()
        config.is_default = True
        config.save()

        self.message_user(request, f"پیکربندی '{config.name}' به عنوان پیش‌فرض تنظیم شد.")

    mark_as_default.short_description = "تنظیم به عنوان پیش‌فرض"

    def test_configuration(self, request, queryset):
        """Test AI configuration"""
        from apps.ai_support.services.ai_service import OpenRouterAIService

        results = []
        for config in queryset:
            try:
                # Test by getting a simple response
                service = OpenRouterAIService()
                response = service.test_config(config)

                if response:
                    results.append(f"✓ {config.name}: موفق")
                else:
                    results.append(f"✗ {config.name}: خطا در دریافت پاسخ")
            except Exception as e:
                results.append(f"✗ {config.name}: {str(e)}")

        self.message_user(request, "\n".join(results))

    test_configuration.short_description = "تست پیکربندی"
