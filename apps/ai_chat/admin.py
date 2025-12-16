# apps/ai_chat/admin.py
from decimal import Decimal

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Sum, Q
from django.utils import timezone
from import_export.admin import ImportExportModelAdmin

from apps.ai_chat.models import AISession, AIMessage, ChatAIConfig, LegalAnalysisLog, GeneralChatAIConfig


class AIMessageInline(admin.TabularInline):
    """Inline for viewing messages within a session"""

    model = AIMessage
    extra = 0
    can_delete = False
    fields = ["created_at", "sender_name", "message_preview", "is_ai", "is_system", "is_read"]
    readonly_fields = ["created_at", "sender_name", "message_preview", "is_ai", "is_system", "is_read"]
    ordering = ["-created_at"]

    def sender_name(self, obj):
        return f"{obj.sender.first_name} {obj.sender.last_name}"

    sender_name.short_description = "فرستنده"

    def message_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content

    message_preview.short_description = "پیش‌نمایش پیام"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AISession)
class AISessionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [
        "colored_pid",
        "user_link",
        "ai_config_link",
        "status_badge",
        "pricing_type_badge",
        "usage_stats",
        "cost_display",
        "message_count",
        "readonly_status",
        "created_time",
    ]
    list_filter = [
        "status",
        "ai_type",
        "is_readonly",
        "paid_with_coins",
        "created_at",
        ("ai_config", admin.RelatedOnlyFieldListFilter),
        ("ai_config__pricing_type", admin.AllValuesFieldListFilter),
    ]
    search_fields = ["pid", "user__email", "user__first_name", "user__last_name", "title"]
    readonly_fields = [
        "pid",
        "created_at",
        "updated_at",
        "usage_chart",
        "cost_breakdown",
        "session_timeline",
        "hybrid_state_display",
    ]

    fieldsets = (
        ("📋 اطلاعات اصلی", {"fields": ("pid", "user", "ai_config", "title", "ai_type")}),
        ("⚙️ تنظیمات", {"fields": ("temperature", "max_tokens", "status"), "classes": ("collapse",)}),
        ("💰 مالی", {"fields": ("fee_amount", "paid_with_coins", "total_cost_coins", "cost_breakdown")}),
        (
            "📊 آمار استفاده",
            {
                "fields": (
                    "total_messages",
                    "total_input_tokens",
                    "total_output_tokens",
                    "total_tokens_used",
                    "total_characters_sent",
                    "usage_chart",
                )
            },
        ),
        ("💎 وضعیت هیبریدی", {"fields": ("hybrid_state_display",), "classes": ("collapse",)}),
        ("💬 پیام‌ها", {"fields": ("unread_messages",)}),
        ("⏱️ زمان", {"fields": ("duration_minutes", "start_date", "end_date", "session_timeline")}),
        ("🔒 وضعیت محدودیت", {"fields": ("is_readonly", "readonly_reason"), "classes": ("collapse",)}),
        ("📅 تاریخچه", {"fields": ("creator", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    inlines = [AIMessageInline]

    actions = ["mark_as_completed", "mark_as_expired", "reactivate_session"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user", "ai_config", "ai_config__general_config")

    def colored_pid(self, obj):
        colors = {
            "active": "#28a745",
            "completed": "#6c757d",
            "expired": "#dc3545",
            "pending": "#ffc107",
        }
        color = colors.get(obj.status, "#007bff")
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.pid)

    colored_pid.short_description = "شناسه"

    def user_link(self, obj):
        url = reverse("admin:user_tainouser_change", args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())

    user_link.short_description = "کاربر"

    def ai_config_link(self, obj):
        if obj.ai_config:
            url = reverse("admin:ai_chat_chataiconfig_change", args=[obj.ai_config.pk])
            return format_html('<a href="{}">{}</a>', url, obj.ai_config.name)
        return "-"

    ai_config_link.short_description = "پیکربندی هوش مصنوعی"

    def status_badge(self, obj):
        badges = {
            "active": ("success", "✓ فعال"),
            "completed": ("secondary", "✓ تکمیل شده"),
            "expired": ("danger", "✗ منقضی شده"),
            "pending": ("warning", "⏳ در انتظار"),
        }
        badge_class, label = badges.get(obj.status, ("info", obj.status))
        return format_html('<span class="badge badge-{}">{}</span>', badge_class, label)

    status_badge.short_description = "وضعیت"

    def pricing_type_badge(self, obj):
        """نمایش نوع قیمت‌گذاری"""
        if not obj.ai_config:
            return "-"

        badges = {
            "message_based": ("warning", "💬 ثابت"),
            "advanced_hybrid": ("info", "💎 هیبریدی"),
        }
        badge_class, label = badges.get(obj.ai_config.pricing_type, ("secondary", "نامشخص"))
        return format_html('<span class="badge badge-{}">{}</span>', badge_class, label)

    pricing_type_badge.short_description = "نوع قیمت"

    def usage_stats(self, obj):
        """نمایش آمار استفاده"""
        stats_html = '<div style="font-size: 11px;">'

        # توکن‌ها
        if obj.total_tokens_used > 0:
            stats_html += f"<div><strong>🔢 توکن:</strong> {obj.total_tokens_used:,}</div>"

        # کاراکترها (برای هیبریدی)
        if obj.ai_config and obj.ai_config.is_advanced_hybrid_pricing():
            stats_html += f"<div><strong>📝 کاراکتر:</strong> {obj.total_characters_sent:,}</div>"

        stats_html += "</div>"
        return format_html(stats_html)

    usage_stats.short_description = "آمار استفاده"

    def cost_display(self, obj):
        if obj.total_cost_coins == 0:
            return format_html('<span style="color: #28a745;">رایگان</span>')
        # Format the number before passing to format_html
        formatted_cost = "{:,.2f}".format(float(obj.total_cost_coins))
        return format_html("<strong>{}</strong> 🪙", formatted_cost)

    cost_display.short_description = "هزینه کل"

    def message_count(self, obj):
        unread = obj.unread_messages
        total = obj.total_messages

        if unread > 0:
            return format_html(
                "<strong>{}</strong> / {} " '<span class="badge badge-danger">{} خوانده نشده</span>', total, total, unread
            )
        return format_html("<strong>{}</strong>", total)

    message_count.short_description = "تعداد پیام"

    def readonly_status(self, obj):
        if obj.is_readonly:
            reasons = {
                "max_messages_reached": "📨 حد پیام",
                "max_tokens_reached": "🔢 حد توکن",
            }
            reason = reasons.get(obj.readonly_reason, obj.readonly_reason)
            return format_html('<span class="badge badge-warning" title="{}">🔒 قفل</span>', reason)
        return format_html('<span class="badge badge-success">🔓 فعال</span>')

    readonly_status.short_description = "قفل/فعال"

    def created_time(self, obj):
        return format_html(
            '<div style="direction: ltr; text-align: left;">{}</div>', obj.created_at.strftime("%Y-%m-%d %H:%M")
        )

    created_time.short_description = "زمان ایجاد"

    def usage_chart(self, obj):
        """نمودار بصری استفاده"""
        if obj.ai_config and obj.ai_config.is_message_based_pricing():
            return format_html(
                '<div style="background: #f0f0f0; padding: 15px; border-radius: 5px;">'
                "<h4>💬 قیمت‌گذاری ثابت</h4>"
                "<div><strong>تعداد پیام:</strong> {}</div>"
                "<div><strong>هزینه هر پیام:</strong> {} سکه</div>"
                "<div><strong>جمع کل:</strong> {:,.2f} سکه</div>"
                "</div>",
                obj.total_messages,
                obj.ai_config.cost_per_message,
                float(obj.total_cost_coins),  # Ensure it's a float
            )

        # For the token chart section - FIXED VERSION:
        if obj.total_tokens_used == 0:
            return "-"

        input_pct = (obj.total_input_tokens / obj.total_tokens_used * 100) if obj.total_tokens_used > 0 else 0
        output_pct = 100 - input_pct

        return format_html(
            '<div style="width: 100%; background: #f0f0f0; border-radius: 5px; overflow: hidden;">'
            '<div style="display: flex; height: 30px;">'
            '<div style="width: {}%; background: #007bff; display: flex; align-items: center; justify-content: center; color: white; font-size: 11px;">'
            "↓ {} ({:.0f}%)"
            "</div>"
            '<div style="width: {}%; background: #28a745; display: flex; align-items: center; justify-content: center; color: white; font-size: 11px;">'
            "↑ {} ({:.0f}%)"
            "</div>"
            "</div>"
            "</div>"
            '<div style="margin-top: 10px;">'
            "<strong>مجموع:</strong> {} توکن"
            "</div>",
            input_pct,
            format(obj.total_input_tokens, ","),  # Format numbers before passing
            input_pct,
            output_pct,
            format(obj.total_output_tokens, ","),
            output_pct,
            format(obj.total_tokens_used, ","),
        )

    usage_chart.short_description = "نمودار مصرف"

    def cost_breakdown(self, obj):
        """جزئیات هزینه بر اساس نوع قیمت‌گذاری"""
        if obj.total_cost_coins == 0:
            return format_html('<div class="alert alert-success">رایگان</div>')

        if not obj.ai_config:

            return format_html(
                '<table class="table table-sm">' "<tr><th>هزینه کل</th><td><strong>{:,.2f}</strong> سکه</td></tr>" "</table>",
                obj.total_cost_coins,
            )

        html = '<table class="table table-sm">'

        if obj.ai_config.is_message_based_pricing():
            # قیمت ثابت
            html += f"<tr><th>نوع قیمت‌گذاری</th><td>💬 ثابت</td></tr>"
            html += f"<tr><th>تعداد پیام‌ها</th><td>{obj.total_messages}</td></tr>"
            html += f"<tr><th>هزینه هر پیام</th><td>{obj.ai_config.cost_per_message} سکه</td></tr>"
            html += f"<tr><th>هزینه کل</th><td><strong>{obj.total_cost_coins:,.2f}</strong> سکه</td></tr>"

        elif obj.ai_config.is_advanced_hybrid_pricing():
            # قیمت هیبریدی
            html += f"<tr><th>نوع قیمت‌گذاری</th><td>💎 هیبریدی پیشرفته</td></tr>"

            if obj.hybrid_base_cost_paid:
                html += f"<tr><th>هزینه پایه</th><td>{obj.ai_config.hybrid_base_cost} سکه ✓</td></tr>"

            if obj.total_characters_sent > 0:
                billable = max(0, obj.total_characters_sent - obj.hybrid_free_chars_used)
                char_cost = billable / obj.ai_config.hybrid_char_per_coin if billable > 0 else 0
                html += f"<tr><th>کاراکترها</th><td>{obj.total_characters_sent:,}</td></tr>"
                html += f"<tr><th>کاراکتر رایگان</th><td>{obj.hybrid_free_chars_used:,}</td></tr>"
                if billable > 0:
                    html += f"<tr><th>کاراکتر قابل محاسبه</th><td>{billable:,} (~{char_cost:.2f} سکه)</td></tr>"

            html += f"<tr style='border-top: 2px solid #dee2e6;'><th>هزینه کل</th><td><strong>{obj.total_cost_coins:,.2f}</strong> سکه</td></tr>"

        html += "</table>"
        return mark_safe(html)

    cost_breakdown.short_description = "جزئیات هزینه"

    def hybrid_state_display(self, obj):
        """نمایش وضعیت هیبریدی"""
        if not obj.ai_config or not obj.ai_config.is_advanced_hybrid_pricing():
            return format_html('<div class="alert alert-info">این جلسه از قیمت‌گذاری هیبریدی استفاده نمی‌کند</div>')

        html = '<div style="background: #e3f2fd; padding: 15px; border-radius: 5px;">'
        html += "<h4>وضعیت قیمت‌گذاری هیبریدی</h4>"

        # هزینه پایه
        if obj.hybrid_base_cost_paid:
            html += "<div>✅ <strong>هزینه پایه پرداخت شده</strong></div>"
        else:
            html += "<div>⏳ <strong>هزینه پایه هنوز پرداخت نشده</strong></div>"

        # کاراکترهای رایگان
        free_remaining = max(0, obj.ai_config.hybrid_free_chars - obj.hybrid_free_chars_used)
        html += f'<div style="margin-top: 10px;">'
        html += f"<strong>کاراکترهای رایگان:</strong><br>"
        html += f"استفاده شده: {obj.hybrid_free_chars_used:,} / {obj.ai_config.hybrid_free_chars:,}<br>"
        html += f"باقیمانده: {free_remaining:,}"
        html += "</div>"

        # نمودار پیشرفت
        if obj.ai_config.hybrid_free_chars > 0:
            used_pct = obj.hybrid_free_chars_used / obj.ai_config.hybrid_free_chars * 100
            html += '<div style="margin-top: 10px; background: #ddd; height: 20px; border-radius: 10px; overflow: hidden;">'
            html += f'<div style="width: {min(used_pct, 100)}%; background: #4caf50; height: 100%;"></div>'
            html += "</div>"

        html += "</div>"
        return mark_safe(html)

    hybrid_state_display.short_description = "وضعیت هیبریدی"

    def session_timeline(self, obj):
        """خط زمانی جلسه"""
        now = timezone.now()

        html = '<div class="timeline" style="position: relative; padding-left: 20px;">'

        # شروع
        html += format_html(
            '<div style="margin-bottom: 15px;">' "<strong>🟢 شروع:</strong> {}" "</div>",
            obj.start_date.strftime("%Y-%m-%d %H:%M") if obj.start_date else "-",
        )

        # پایان
        if obj.end_date:
            if obj.end_date < now:
                color = "red"
                icon = "🔴"
            else:
                color = "orange"
                icon = "🟠"

            html += format_html(
                '<div style="margin-bottom: 15px;">'
                "<strong>{} پایان:</strong> {} "
                '<span style="color: {};">({})</span>'
                "</div>",
                icon,
                obj.end_date.strftime("%Y-%m-%d %H:%M"),
                color,
                "منقضی شده" if obj.end_date < now else "فعال",
            )

        # مدت
        html += format_html("<div><strong>⏱️ مدت:</strong> {} دقیقه</div>", obj.duration_minutes)

        html += "</div>"
        return mark_safe(html)

    session_timeline.short_description = "خط زمانی جلسه"

    # Actions
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status="completed")
        self.message_user(request, f"{updated} جلسه به عنوان تکمیل شده علامت‌گذاری شد.")

    mark_as_completed.short_description = "علامت‌گذاری به عنوان تکمیل شده"

    def mark_as_expired(self, request, queryset):
        updated = queryset.update(status="expired")
        self.message_user(request, f"{updated} جلسه به عنوان منقضی شده علامت‌گذاری شد.")

    mark_as_expired.short_description = "علامت‌گذاری به عنوان منقضی شده"

    def reactivate_session(self, request, queryset):
        updated = queryset.update(status="active", is_readonly=False)
        self.message_user(request, f"{updated} جلسه فعال شد.")

    reactivate_session.short_description = "فعال‌سازی مجدد جلسه"


@admin.register(AIMessage)
class AIMessageAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [
        "colored_pid",
        "session_link",
        "sender_info",
        "message_type_badge",
        "message_preview",
        "ai_status",
        "read_status",
        "created_time",
    ]
    list_filter = [
        "message_type",
        "is_ai",
        "is_system",
        "is_read",
        "is_failed",
        "created_at",
        ("ai_session", admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = ["pid", "content", "sender__email", "sender__first_name", "sender__last_name", "ai_session__pid"]
    readonly_fields = ["pid", "created_at", "updated_at", "full_content_display", "attachment_preview"]

    fieldsets = (
        ("📋 اطلاعات اصلی", {"fields": ("pid", "ai_session", "sender", "message_type")}),
        ("💬 محتوا", {"fields": ("full_content_display", "attachment", "attachment_preview")}),
        ("🤖 وضعیت", {"fields": ("is_ai", "is_system", "is_read", "read_at")}),
        ("⚠️ خطا", {"fields": ("is_failed", "failure_reason"), "classes": ("collapse",)}),
        ("📅 تاریخچه", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("sender", "ai_session", "attachment")

    def colored_pid(self, obj):
        color = "#007bff" if obj.is_ai else "#28a745"
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.pid)

    colored_pid.short_description = "شناسه"

    def session_link(self, obj):
        url = reverse("admin:ai_chat_aisession_change", args=[obj.ai_session.pk])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.ai_session.title[:30] + "..." if len(obj.ai_session.title) > 30 else obj.ai_session.title,
        )

    session_link.short_description = "جلسه"

    def sender_info(self, obj):
        return format_html(
            '<div><strong>{}</strong><br><small style="color: #6c757d;">{}</small></div>',
            obj.sender.get_full_name(),
            obj.sender.email,
        )

    sender_info.short_description = "فرستنده"

    def message_type_badge(self, obj):
        badges = {
            "text": ("primary", "📝 متن"),
            "image": ("info", "🖼️ تصویر"),
            "file": ("secondary", "📎 فایل"),
            "system": ("warning", "⚙️ سیستم"),
        }
        badge_class, label = badges.get(obj.message_type, ("light", obj.message_type))
        return format_html('<span class="badge badge-{}">{}</span>', badge_class, label)

    message_type_badge.short_description = "نوع"

    def message_preview(self, obj):
        preview = obj.content[:60] + "..." if len(obj.content) > 60 else obj.content
        return format_html(
            '<div style="max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{}">{}</div>',
            obj.content,
            preview,
        )

    message_preview.short_description = "پیش‌نمایش"

    def ai_status(self, obj):
        if obj.is_ai:
            return format_html('<span class="badge badge-info">🤖 هوش مصنوعی</span>')
        elif obj.is_system:
            return format_html('<span class="badge badge-warning">⚙️ سیستم</span>')
        return format_html('<span class="badge badge-success">👤 کاربر</span>')

    ai_status.short_description = "وضعیت"

    def read_status(self, obj):
        if obj.is_read:
            return format_html(
                '<span class="badge badge-success" title="{}">✓ خوانده شده</span>',
                obj.read_at.strftime("%Y-%m-%d %H:%M") if obj.read_at else "",
            )
        return format_html('<span class="badge badge-secondary">خوانده نشده</span>')

    read_status.short_description = "وضعیت خواندن"

    def created_time(self, obj):
        return format_html(
            '<div style="direction: ltr; text-align: left;">{}</div>', obj.created_at.strftime("%Y-%m-%d %H:%M")
        )

    created_time.short_description = "زمان"

    def full_content_display(self, obj):
        return format_html(
            '<div style="max-width: 600px; padding: 10px; background: #f8f9fa; border-radius: 5px; white-space: pre-wrap;">{}</div>',
            obj.content,
        )

    full_content_display.short_description = "محتوای کامل"

    def attachment_preview(self, obj):
        if obj.attachment:
            url = reverse("admin:document_tainodocument_change", args=[obj.attachment.pk])
            return format_html('<a href="{}" target="_blank">📎 مشاهده فایل پیوست</a>', url)
        return "-"

    attachment_preview.short_description = "پیوست"


@admin.register(GeneralChatAIConfig)
class GeneralChatAIConfigAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [
        "colored_name",
        "static_name",
        "ai_configs_count",
        "limits_display",
        "order",
        "active_badge",
        "created_time",
    ]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "static_name", "description"]
    readonly_fields = ["pid", "created_at", "updated_at", "icon_preview", "related_configs"]

    fieldsets = (
        ("📋 اطلاعات اصلی", {"fields": ("pid", "name", "static_name", "description", "system_instruction")}),
        ("🔢 محدودیت‌ها", {"fields": ("max_messages_per_chat", "max_tokens_per_chat")}),
        ("🎨 نمایش", {"fields": ("order", "icon", "icon_preview")}),
        ("🔗 پیکربندی‌های مرتبط", {"fields": ("related_configs",), "classes": ("collapse",)}),
        ("📅 تاریخچه", {"fields": ("creator", "is_active", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(configs_count=Count("ai_configs", filter=Q(ai_configs__is_active=True)))

    def colored_name(self, obj):
        return format_html('<strong style="color: #007bff; font-size: 14px;">{}</strong>', obj.name)

    colored_name.short_description = "نام"

    def ai_configs_count(self, obj):
        count = obj.configs_count
        if count == 0:
            return format_html('<span style="color: #dc3545;">0</span>')
        return format_html('<span class="badge badge-info">{} پیکربندی</span>', count)

    ai_configs_count.short_description = "تعداد پیکربندی"

    def limits_display(self, obj):
        try:
            max_messages = obj.max_messages_per_chat or 0
            max_tokens = obj.max_tokens_per_chat or 0
            max_tokens_formatted = f"{max_tokens:,}"

            return format_html(
                "<div>" "<strong>پیام:</strong> {} | " "<strong>توکن:</strong> {}" "</div>",
                max_messages,
                max_tokens_formatted,
            )
        except (TypeError, ValueError):
            return format_html(
                "<div>" "<strong>پیام:</strong> {} | " "<strong>توکن:</strong> {}" "</div>",
                obj.max_messages_per_chat,
                obj.max_tokens_per_chat,
            )

    limits_display.short_description = "محدودیت‌ها"

    def active_badge(self, obj):
        if obj.is_active:
            return format_html('<span class="badge badge-success">✓ فعال</span>')
        return format_html('<span class="badge badge-danger">✗ غیرفعال</span>')

    active_badge.short_description = "وضعیت"

    def created_time(self, obj):
        return format_html('<div style="direction: ltr; text-align: left;">{}</div>', obj.created_at.strftime("%Y-%m-%d"))

    created_time.short_description = "تاریخ ایجاد"

    def icon_preview(self, obj):
        if obj.icon:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px; border-radius: 5px;" />', obj.icon.url
            )
        return "-"

    icon_preview.short_description = "پیش‌نمایش آیکون"

    def related_configs(self, obj):
        configs = obj.ai_configs.filter(is_active=True)
        if not configs.exists():
            return format_html('<div class="alert alert-info">هیچ پیکربندی فعالی وجود ندارد</div>')

        html = '<table class="table table-sm">'
        html += "<thead><tr><th>نام</th><th>قدرت</th><th>قیمت‌گذاری</th><th>مدل</th><th>وضعیت</th></tr></thead><tbody>"

        for config in configs:
            pricing_badge = "💬 ثابت" if config.is_message_based_pricing() else "💎 هیبریدی"

            html += format_html(
                "<tr>" '<td><a href="{}">{}</a></td>' "<td>{}</td>" "<td>{}</td>" "<td>{}</td>" "<td>{}</td>" "</tr>",
                reverse("admin:ai_chat_chataiconfig_change", args=[config.pk]),
                config.name,
                config.get_strength_display(),
                pricing_badge,
                config.model_name,
                "✓" if config.is_active else "✗",
            )

        html += "</tbody></table>"
        return mark_safe(html)

    related_configs.short_description = "پیکربندی‌های مرتبط"


@admin.register(ChatAIConfig)
class ChatAIConfigAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [
        "colored_name",
        "general_config_link",
        "strength_badge",
        "model_info",
        "pricing_type_badge",
        "cost_preview",
        "default_badge",
        "active_badge",
        "created_time",
    ]
    list_filter = [
        "strength",
        "pricing_type",
        "is_default",
        "is_active",
        "created_at",
        ("general_config", admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = ["name", "static_name", "model_name", "description"]
    readonly_fields = [
        "pid",
        "created_at",
        "updated_at",
        "pricing_calculator",
        "combined_prompt_preview",
        "step_options_preview",
    ]

    fieldsets = (
        ("📋 اطلاعات اصلی", {"fields": ("pid", "general_config", "name", "strength", "static_name", "description")}),
        ("🤖 پیکربندی مدل", {"fields": ("model_name", "base_url", "api_key", "system_prompt", "combined_prompt_preview")}),
        ("⚙️ پارامترها", {"fields": ("default_temperature", "default_max_tokens", "rate_limit_per_minute")}),
        (
            "💰 نوع قیمت‌گذاری",
            {
                "fields": ("pricing_type",),
            },
        ),
        (
            "💬 قیمت ثابت (Message-Based)",
            {"fields": ("cost_per_message",), "classes": ("collapse",), "description": "برای قیمت‌گذاری ثابت"},
        ),
        (
            "💎 قیمت هیبریدی (Advanced Hybrid)",
            {
                "fields": (
                    "hybrid_base_cost",
                    "hybrid_char_per_coin",
                    "hybrid_free_chars",
                    "hybrid_tokens_min",
                    "hybrid_tokens_max",
                    "hybrid_tokens_step",
                    "hybrid_cost_per_step",
                    "free_pages",
                    "cost_per_page",
                    "max_pages_per_request",
                    "free_minutes",
                    "cost_per_minute",
                    "max_minutes_per_request",
                    "step_options_preview",
                ),
                "classes": ("collapse",),
                "description": "برای قیمت‌گذاری هیبریدی پیشرفته",
            },
        ),
        ("🧮 ماشین حساب قیمت", {"fields": ("pricing_calculator",), "classes": ("collapse",)}),
        ("🎯 تنظیمات", {"fields": ("order", "is_default", "is_active")}),
        ("🔗 سرویس مرتبط", {"fields": ("related_service",), "classes": ("collapse",)}),
        ("📅 تاریخچه", {"fields": ("creator", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("general_config", "creator")

    def colored_name(self, obj):
        return format_html('<strong style="color: #007bff;">{}</strong>', obj.name)

    colored_name.short_description = "نام"

    def general_config_link(self, obj):
        if obj.general_config:
            url = reverse("admin:ai_chat_generalchataiconfig_change", args=[obj.general_config.pk])
            return format_html('<a href="{}">{}</a>', url, obj.general_config.name)
        return "-"

    general_config_link.short_description = "پیکربندی عمومی"

    def strength_badge(self, obj):
        badges = {
            "medium": ("secondary", "⚪ متوسط"),
            "strong": ("primary", "🔵 قوی"),
            "very_strong": ("success", "🟢 خیلی قوی"),
            "special": ("warning", "⭐ ویژه"),
            "unique": ("info", "⭐ یکتا"),
        }
        badge_class, label = badges.get(obj.strength, ("light", obj.strength))
        return format_html('<span class="badge badge-{}">{}</span>', badge_class, label)

    strength_badge.short_description = "قدرت"

    def pricing_type_badge(self, obj):
        """نمایش نوع قیمت‌گذاری"""
        badges = {
            "message_based": ("warning", "💬 ثابت"),
            "advanced_hybrid": ("info", "💎 هیبریدی"),
        }
        badge_class, label = badges.get(obj.pricing_type, ("light", obj.pricing_type))
        return format_html('<span class="badge badge-{}">{}</span>', badge_class, label)

    pricing_type_badge.short_description = "نوع قیمت"

    def model_info(self, obj):
        return format_html(
            "<div>" "<strong>{}</strong><br>" '<small style="color: #6c757d;">T: {} | Max: {}</small>' "</div>",
            obj.model_name,
            obj.default_temperature,
            obj.default_max_tokens,
        )

    model_info.short_description = "مدل"

    def cost_preview(self, obj):
        if obj.is_message_based_pricing():
            formatted_cost = "{:.2f}".format(float(obj.cost_per_message))
            return format_html('<div style="font-size: 11px;">💬 <strong>{}</strong> سکه/پیام</div>', formatted_cost)

        elif obj.is_advanced_hybrid_pricing():
            return format_html(
                '<div style="font-size: 10px;">'
                "💎 پایه: <strong>{}</strong> سکه<br>"
                "📝 {}/سکه کاراکتر<br>"
                "🔢 {}/استپ سکه"
                "</div>",
                float(obj.hybrid_base_cost),
                obj.hybrid_char_per_coin,
                float(obj.hybrid_cost_per_step),
            )

        return "-"

    cost_preview.short_description = "پیش‌نمایش هزینه"

    def default_badge(self, obj):
        if obj.is_default:
            return format_html('<span class="badge badge-warning">⭐ پیش‌فرض</span>')
        return "-"

    default_badge.short_description = "پیش‌فرض"

    def active_badge(self, obj):
        if obj.is_active:
            return format_html('<span class="badge badge-success">✓ فعال</span>')
        return format_html('<span class="badge badge-danger">✗ غیرفعال</span>')

    active_badge.short_description = "وضعیت"

    def created_time(self, obj):
        return format_html('<div style="direction: ltr; text-align: left;">{}</div>', obj.created_at.strftime("%Y-%m-%d"))

    created_time.short_description = "تاریخ ایجاد"

    def pricing_calculator(self, obj):
        """ماشین حساب تعاملی هزینه"""

        if obj.is_message_based_pricing():
            # قیمت ثابت - ساده
            cost = float(obj.cost_per_message)

            html = f"""
            <div class="pricing-calc" style="background: #fff3cd; padding: 20px; border-radius: 5px;">
                <h3>💬 ماشین حساب قیمت ثابت</h3>

                <table class="table table-sm">
                    <tr>
                        <th>هزینه هر پیام</th>
                        <td><strong>{cost:.2f}</strong> سکه</td>
                    </tr>
                    <tr>
                        <th>مثال: 10 پیام</th>
                        <td><strong>{cost * 10:.2f}</strong> سکه</td>
                    </tr>
                    <tr>
                        <th>مثال: 50 پیام</th>
                        <td><strong>{cost * 50:.2f}</strong> سکه</td>
                    </tr>
                    <tr style="border-top: 2px solid #dee2e6;">
                        <th>مثال: 100 پیام</th>
                        <td><strong>{cost * 100:.2f}</strong> سکه</td>
                    </tr>
                </table>

                <small class="text-muted">
                    💡 هر پیام کاربر با هزینه ثابت محاسبه می‌شود
                </small>
            </div>
            """
            return mark_safe(html)

        elif obj.is_advanced_hybrid_pricing():
            # قیمت هیبریدی - پیچیده
            base_cost = float(obj.hybrid_base_cost)
            char_per_coin = obj.hybrid_char_per_coin
            free_chars = obj.hybrid_free_chars
            min_tokens = obj.hybrid_tokens_min
            step_size = obj.hybrid_tokens_step
            cost_per_step = float(obj.hybrid_cost_per_step)

            # سناریوهای مثال
            scenarios = [
                ("کوتاه", 3000, 1000),  # کمتر از free_chars
                ("متوسط", 7500, 2000),  # بیشتر از free_chars
                ("بلند", 15000, 4000),  # خیلی بیشتر
            ]

            html = f"""
            <div class="pricing-calc" style="background: #e3f2fd; padding: 20px; border-radius: 5px;">
                <h3>💎 ماشین حساب قیمت هیبریدی</h3>

                <div style="background: #fff; padding: 15px; margin: 15px 0; border-radius: 3px;">
                    <h4>📊 تنظیمات:</h4>
                    <ul style="margin: 0;">
                        <li><strong>هزینه پایه:</strong> {base_cost} سکه (یکبار)</li>
                        <li><strong>کاراکتر:</strong> هر {char_per_coin:,} کاراکتر = 1 سکه</li>
                        <li><strong>رایگان:</strong> {free_chars:,} کاراکتر اول</li>
                        <li><strong>استپ:</strong> هر {step_size} توکن = {cost_per_step} سکه</li>
                    </ul>
                </div>

                <table class="table table-sm table-bordered">
                    <thead style="background: #bbdefb;">
                        <tr>
                            <th>سناریو</th>
                            <th>کاراکتر</th>
                            <th>توکن</th>
                            <th>هزینه پایه</th>
                            <th>هزینه کاراکتر</th>
                            <th>هزینه استپ</th>
                            <th>جمع کل</th>
                        </tr>
                    </thead>
                    <tbody>
            """

            for scenario_name, chars, tokens in scenarios:
                # محاسبه هزینه کاراکتر
                billable_chars = max(0, chars - free_chars)
                char_cost = billable_chars / char_per_coin if billable_chars > 0 else 0

                # محاسبه هزینه استپ
                import math

                tokens_above_min = max(0, tokens - min_tokens)
                num_steps = math.ceil(tokens_above_min / step_size) if tokens_above_min > 0 else 0
                step_cost = num_steps * cost_per_step

                # جمع کل (فرض: پیام اول)
                total = base_cost + char_cost + step_cost

                html += f"""
                    <tr>
                        <td><strong>{scenario_name}</strong></td>
                        <td>{chars:,}</td>
                        <td>{tokens}</td>
                        <td>{base_cost:.2f}</td>
                        <td>{char_cost:.2f}</td>
                        <td>{step_cost:.2f}</td>
                        <td><strong>{total:.2f}</strong></td>
                    </tr>
                """

            html += """
                    </tbody>
                </table>

                <div style="margin-top: 15px; padding: 10px; background: #fff9c4; border-radius: 3px;">
                    <small>
                        <strong>💡 نکته:</strong> هزینه پایه فقط برای اولین پیام جلسه محاسبه می‌شود.
                        پیام‌های بعدی فقط هزینه کاراکتر و استپ دارند.
                    </small>
                </div>
            </div>
            """
            return mark_safe(html)

        return "-"

    pricing_calculator.short_description = "ماشین حساب هزینه"

    def step_options_preview(self, obj):
        """پیش‌نمایش گزینه‌های استپ با نمایش بهتر"""
        if not obj.is_advanced_hybrid_pricing():
            return format_html('<div class="alert alert-info">این کانفیگ از قیمت‌گذاری هیبریدی استفاده نمی‌کند</div>')

        options = obj.get_step_options()

        if not options:
            return format_html('<div class="alert alert-warning">هیچ گزینه استپی یافت نشد</div>')

        # محاسبه آمار
        total_options = len(options)
        min_cost = Decimal(str(options[0]["step_cost"])) if options else Decimal("0")
        max_cost = Decimal(str(options[-1]["step_cost"])) if options else Decimal("0")

        html = '<div style="background: #f5f5f5; padding: 15px; border-radius: 5px;">'
        html += "<h4>🎚️ گزینه‌های استپ:</h4>"

        # نمایش آمار کلی
        html += '<div style="background: #e3f2fd; padding: 10px; margin-bottom: 15px; border-radius: 3px;">'
        html += f"<strong>تعداد کل گزینه‌ها:</strong> {total_options}<br>"
        html += f"<strong>محدوده توکن:</strong> {obj.hybrid_tokens_min:,} - {obj.hybrid_tokens_max:,}<br>"
        html += f"<strong>اندازه هر استپ:</strong> {obj.hybrid_tokens_step:,} توکن<br>"
        html += f"<strong>هزینه هر استپ:</strong> {obj.hybrid_cost_per_step} سکه<br>"
        html += f"<strong>هزینه هر صفحه:</strong> {obj.cost_per_page} سکه<br>"
        html += f"<strong>تعداد صفحات رایگان:</strong> {obj.free_pages} سکه<br>"
        html += f"<strong>هزینه هر دقیقه:</strong> {obj.cost_per_minute} سکه<br>"
        html += f"<strong>تعداد دقایق صوتی رایگان:</strong> {obj.free_minutes} سکه<br>"
        html += f"<strong>محدوده هزینه:</strong> {min_cost:.2f} - {max_cost:.2f} سکه"
        html += "</div>"

        html += '<table class="table table-sm table-striped">'
        html += "<thead><tr>"
        html += "<th>ردیف</th>"
        html += "<th>مقدار توکن</th>"
        html += "<th>تعداد استپ</th>"
        html += "<th>هزینه استپ (سکه)</th>"
        html += "<th>هزینه کل با پایه (سکه)</th>"
        html += "</tr></thead>"
        html += "<tbody>"

        # نمایش گزینه‌ها
        display_count = min(15, total_options)  # نمایش 15 گزینه اول

        for i, option in enumerate(options[:display_count], 1):
            # تبدیل step_cost به Decimal برای جمع با hybrid_base_cost
            step_cost = Decimal(str(option["step_cost"]))
            total_with_base = obj.hybrid_base_cost + step_cost

            # رنگ‌بندی ردیف‌ها
            row_class = ""
            if i % 5 == 0:
                row_class = 'style="background: #fff3cd;"'  # هر 5 ردیف زرد

            html += f"<tr {row_class}>"
            html += f"<td>{i}</td>"
            html += f"<td><strong>{option['value']:,}</strong></td>"
            html += f"<td>{option['steps']}</td>"
            html += f"<td>{step_cost:.2f}</td>"
            html += f"<td><strong>{total_with_base:.2f}</strong></td>"
            html += "</tr>"

        if total_options > display_count:
            html += f'<tr><td colspan="5" style="text-align: center;">'
            html += f"<em>... و {total_options - display_count} گزینه دیگر</em>"
            html += "</td></tr>"

        html += "</tbody></table>"

        # راهنما
        html += '<div style="margin-top: 10px; padding: 10px; background: #fff9c4; border-radius: 3px;">'
        html += "<small><strong>💡 نکته:</strong> "
        html += "هزینه کل = هزینه پایه + هزینه استپ + هزینه کاراکتر"
        html += "</small></div>"

        html += "</div>"

        return mark_safe(html)

    step_options_preview.short_description = "گزینه‌های استپ"

    def combined_prompt_preview(self, obj):
        """پیش‌نمایش پرامپت ترکیبی"""
        combined = obj.get_combined_system_prompt()
        return format_html(
            '<div style="max-width: 700px; padding: 10px; background: #f8f9fa; border-radius: 5px; white-space: pre-wrap; max-height: 300px; overflow-y: auto;">{}</div>',
            combined,
        )

    combined_prompt_preview.short_description = "پیش‌نمایش پرامپت ترکیبی"


@admin.register(LegalAnalysisLog)
class LegalAnalysisLogAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [
        "colored_pid",
        "user_link",
        "ai_type_badge",
        "request_type",
        "analysis_preview",
        "session_link",
        "content_only_badge",
        "created_time",
    ]
    list_filter = [
        "ai_type",
        "user_request_choice",
        "is_content_only",
        "created_at",
        ("ai_session", admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        "pid",
        "user__email",
        "user__first_name",
        "user__last_name",
        "analysis_text",
        "user_request_analysis_text",
    ]
    readonly_fields = ["pid", "created_at", "updated_at", "full_analysis_display", "user_request_display", "openai_details"]

    fieldsets = (
        ("📋 اطلاعات اصلی", {"fields": ("pid", "user", "ai_type", "user_request_choice")}),
        ("📄 تحلیل", {"fields": ("full_analysis_display",)}),
        ("💬 درخواست کاربر", {"fields": ("user_request_display",), "classes": ("collapse",)}),
        ("🔗 ارتباطات", {"fields": ("ai_session", "is_content_only")}),
        ("🤖 جزئیات OpenAI", {"fields": ("openai_details", "assistant_id", "thread_id", "run_id"), "classes": ("collapse",)}),
        ("📅 تاریخچه", {"fields": ("is_active", "is_deleted", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user", "ai_session")

    def colored_pid(self, obj):
        return format_html('<span style="color: #6f42c1; font-weight: bold;">{}</span>', obj.pid)

    colored_pid.short_description = "شناسه"

    def user_link(self, obj):
        url = reverse("admin:user_tainouser_change", args=[obj.user.pk])
        return format_html(
            '<a href="{}">{}</a><br><small style="color: #6c757d;">{}</small>', url, obj.user.get_full_name(), obj.user.email
        )

    user_link.short_description = "کاربر"

    def ai_type_badge(self, obj):
        badges = {
            "v": ("primary", "V"),
            "v_plus": ("info", "V+"),
            "v_x": ("success", "VX"),
        }
        badge_class, label = badges.get(obj.ai_type, ("secondary", obj.ai_type))
        return format_html('<span class="badge badge-{}">🤖 {}</span>', badge_class, label)

    ai_type_badge.short_description = "نوع هوش مصنوعی"

    def request_type(self, obj):
        if obj.user_request_choice:
            return format_html('<span class="badge badge-info">{}</span>', obj.user_request_choice)
        return "-"

    request_type.short_description = "نوع درخواست"

    def analysis_preview(self, obj):
        if obj.analysis_text:
            preview = obj.analysis_text[:80] + "..." if len(obj.analysis_text) > 80 else obj.analysis_text
            return format_html('<div style="max-width: 300px;" title="{}">{}</div>', obj.analysis_text, preview)
        return "-"

    analysis_preview.short_description = "پیش‌نمایش تحلیل"

    def session_link(self, obj):
        if obj.ai_session:
            url = reverse("admin:ai_chat_aisession_change", args=[obj.ai_session.pk])
            return format_html('<a href="{}">📱 مشاهده جلسه</a>', url)
        return "-"

    session_link.short_description = "جلسه"

    def content_only_badge(self, obj):
        if obj.is_content_only:
            return format_html('<span class="badge badge-warning">📝 فقط متن</span>')
        return format_html('<span class="badge badge-info">📎 با فایل</span>')

    content_only_badge.short_description = "نوع محتوا"

    def created_time(self, obj):
        return format_html(
            '<div style="direction: ltr; text-align: left;">{}</div>', obj.created_at.strftime("%Y-%m-%d %H:%M")
        )

    created_time.short_description = "زمان"

    def full_analysis_display(self, obj):
        if obj.analysis_text:
            return format_html(
                '<div style="max-width: 700px; padding: 15px; background: #f8f9fa; border-radius: 5px; white-space: pre-wrap; max-height: 400px; overflow-y: auto;">{}</div>',
                obj.analysis_text,
            )
        return format_html('<div class="alert alert-info">تحلیلی موجود نیست</div>')

    full_analysis_display.short_description = "تحلیل کامل"

    def user_request_display(self, obj):
        if obj.user_request_analysis_text:
            return format_html(
                '<div style="max-width: 700px; padding: 15px; background: #fff3cd; border-radius: 5px; white-space: pre-wrap; max-height: 400px; overflow-y: auto;">{}</div>',
                obj.user_request_analysis_text,
            )
        return format_html('<div class="alert alert-info">درخواست کاربر موجود نیست</div>')

    user_request_display.short_description = "درخواست کاربر"

    def openai_details(self, obj):
        if not any([obj.assistant_id, obj.thread_id, obj.run_id]):
            return format_html('<div class="alert alert-info">جزئیات OpenAI موجود نیست</div>')

        html = '<table class="table table-sm">'
        if obj.assistant_id:
            html += format_html("<tr><th>Assistant ID</th><td><code>{}</code></td></tr>", obj.assistant_id)
        if obj.thread_id:
            html += format_html("<tr><th>Thread ID</th><td><code>{}</code></td></tr>", obj.thread_id)
        if obj.run_id:
            html += format_html("<tr><th>Run ID</th><td><code>{}</code></td></tr>", obj.run_id)
        html += "</table>"

        return mark_safe(html)

    openai_details.short_description = "جزئیات OpenAI"
