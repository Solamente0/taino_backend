from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    TermsOfUse,
    FrequentlyAskedQuestion,
    ContactUs,
    Newsletter,
    ServiceItem,
    ServiceCategory,
    AboutUs,
    AboutUsTeamMember,
    TutorialVideo,
)


@admin.register(TermsOfUse)
class TermsOfUseAdmin(admin.ModelAdmin):
    list_display = ["title", "order", "parent", "is_active", "created_at"]
    list_filter = ["is_active", "created_at", "parent"]
    search_fields = ["title", "content"]
    list_editable = ["order", "is_active"]
    ordering = ["order"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("اطلاعات اصلی", {"fields": ("title", "content", "parent")}),
        ("تنظیمات", {"fields": ("order", "is_active")}),
        ("زمان‌بندی", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(FrequentlyAskedQuestion)
class FrequentlyAskedQuestionAdmin(admin.ModelAdmin):
    list_display = ["question", "order", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["question", "answer"]
    list_editable = ["order", "is_active"]
    ordering = ["order"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("سوال و پاسخ", {"fields": ("question", "answer")}),
        ("تنظیمات", {"fields": ("order", "is_active")}),
        ("زمان‌بندی", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    list_display = ["subject", "email", "phone", "is_read", "created_at"]
    list_filter = ["is_read", "created_at"]
    search_fields = ["email", "phone", "subject", "message", "name", "description"]
    list_editable = ["is_read"]
    readonly_fields = ["created_at", "updated_at", "email", "phone", "subject", "message", "name", "description"]
    ordering = ["-created_at"]

    fieldsets = (
        ("اطلاعات تماس", {"fields": ("name", "email", "phone")}),
        ("پیام", {"fields": ("subject", "message", "description")}),
        ("وضعیت", {"fields": ("is_read",)}),
        ("زمان‌بندی", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    actions = ["mark_as_read", "mark_as_unread"]

    @admin.action(description="علامت‌گذاری به عنوان خوانده شده")
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} پیام به عنوان خوانده شده علامت‌گذاری شد.")

    @admin.action(description="علامت‌گذاری به عنوان خوانده نشده")
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} پیام به عنوان خوانده نشده علامت‌گذاری شد.")


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ["email", "is_active", "created_at", "unsubscribe_link"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["email"]
    list_editable = ["is_active"]
    readonly_fields = ["created_at", "updated_at", "unsubscribe_token", "unsubscribe_url"]
    ordering = ["-created_at"]

    fieldsets = (
        ("اطلاعات اشتراک", {"fields": ("email", "is_active")}),
        ("لینک لغو اشتراک", {"fields": ("unsubscribe_token", "unsubscribe_url"), "classes": ("collapse",)}),
        ("زمان‌بندی", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def unsubscribe_link(self, obj):
        if obj.unsubscribe_token:
            return format_html('<a href="#" title="{}">لینک لغو اشتراک</a>', obj.unsubscribe_token[:20] + "...")
        return "-"

    unsubscribe_link.short_description = "لینک لغو اشتراک"

    def unsubscribe_url(self, obj):
        if obj.unsubscribe_token:
            # Adjust this URL based on your actual unsubscribe endpoint
            url = f"/newsletter/unsubscribe/{obj.unsubscribe_token}/"
            return format_html('<a href="{}" target="_blank">{}</a>', url, url)
        return "-"

    unsubscribe_url.short_description = "URL لغو اشتراک"

    actions = ["activate_subscriptions", "deactivate_subscriptions"]

    @admin.action(description="فعال‌سازی اشتراک")
    def activate_subscriptions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} اشتراک فعال شد.")

    @admin.action(description="غیرفعال‌سازی اشتراک")
    def deactivate_subscriptions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} اشتراک غیرفعال شد.")


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "static_name", "order", "soon", "is_active", "icon_preview", "services_count", "parent"]
    list_filter = ["is_active", "soon", "created_at", "parent"]
    search_fields = ["name", "static_name", "description", "parent"]
    list_editable = ["order", "is_active", "soon"]
    ordering = ["order"]
    readonly_fields = ["created_at", "updated_at", "icon_preview"]
    filter_horizontal = ["roles"]

    fieldsets = (
        ("اطلاعات اصلی", {"fields": ("name", "static_name", "description", "parent")}),
        ("تصاویر", {"fields": ("icon", "icon_preview")}),
        ("مسیریابی", {"fields": ("frontend_route", "roles")}),
        ("تنظیمات", {"fields": ("order", "soon", "is_active")}),
        ("زمان‌بندی", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def icon_preview(self, obj):
        if obj.icon and obj.icon.file:
            return format_html('<img src="{}" width="50" height="50" />', obj.icon.file.url)
        return "-"

    icon_preview.short_description = "پیش‌نمایش آیکون"

    def services_count(self, obj):
        count = obj.service_items.filter(is_active=True).count()
        url = reverse("admin:common_serviceitem_changelist") + f"?category__id__exact={obj.id}"
        return format_html('<a href="{}">{} سرویس</a>', url, count)

    services_count.short_description = "تعداد سرویس‌ها"


@admin.register(ServiceItem)
class ServiceItemAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "static_name", "order", "soon", "is_active", "icon_preview"]
    list_filter = ["is_active", "soon", "category", "created_at"]
    search_fields = ["name", "static_name", "description"]
    list_editable = ["order", "is_active", "soon"]
    ordering = ["category", "order"]
    readonly_fields = ["created_at", "updated_at", "icon_preview"]
    filter_horizontal = ["roles"]
    autocomplete_fields = ["category"]

    fieldsets = (
        ("اطلاعات اصلی", {"fields": ("name", "static_name", "description", "category")}),
        ("تصاویر", {"fields": ("icon", "icon_preview")}),
        ("مسیریابی", {"fields": ("frontend_route", "roles")}),
        ("تنظیمات", {"fields": ("order", "soon", "is_active")}),
        ("زمان‌بندی", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def icon_preview(self, obj):
        if obj.icon and obj.icon.file:
            return format_html('<img src="{}" width="50" height="50" />', obj.icon.file.url)
        return "-"

    icon_preview.short_description = "پیش‌نمایش آیکون"


class AboutUsTeamMemberInline(admin.TabularInline):
    model = AboutUsTeamMember
    extra = 1
    fields = ["full_name", "job_title", "resume_link", "avatar", "order", "is_active"]
    readonly_fields = []
    ordering = ["order"]


@admin.register(AboutUs)
class AboutUsAdmin(admin.ModelAdmin):
    list_display = ["title", "is_active", "team_members_count", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["title", "history", "values", "services"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [AboutUsTeamMemberInline]

    fieldsets = (
        ("عنوان", {"fields": ("title",)}),
        ("محتوا", {"fields": ("history", "values", "services", "team_description", "extra")}),
        ("تنظیمات", {"fields": ("is_active",)}),
        ("زمان‌بندی", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def team_members_count(self, obj):
        count = obj.team_members.filter(is_active=True).count()
        return f"{count} نفر"

    team_members_count.short_description = "اعضای تیم"


@admin.register(AboutUsTeamMember)
class AboutUsTeamMemberAdmin(admin.ModelAdmin):
    list_display = ["full_name", "job_title", "about_us", "order", "is_active", "avatar_preview"]
    list_filter = ["is_active", "about_us", "created_at"]
    search_fields = ["full_name", "job_title"]
    list_editable = ["order", "is_active"]
    ordering = ["about_us", "order"]
    readonly_fields = ["created_at", "updated_at", "avatar_preview"]
    autocomplete_fields = ["about_us"]

    fieldsets = (
        ("اطلاعات شخصی", {"fields": ("full_name", "job_title", "resume_link")}),
        ("تصویر", {"fields": ("avatar", "avatar_preview")}),
        ("تنظیمات", {"fields": ("about_us", "order", "is_active")}),
        ("زمان‌بندی", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def avatar_preview(self, obj):
        if obj.avatar and obj.avatar.file:
            return format_html('<img src="{}" width="100" height="100" style="border-radius: 50%;" />', obj.avatar.file.url)
        return "-"

    avatar_preview.short_description = "پیش‌نمایش تصویر"


@admin.register(TutorialVideo)
class TutorialVideoAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "route_path",
        "duration",
        "show_on_first_visit",
        "order",
        "is_active",
        "video_source_type",
        "created_at",
    ]
    list_filter = ["is_active", "show_on_first_visit", "created_at"]
    search_fields = ["title", "route_path", "description", "tags"]
    list_editable = ["order", "is_active", "show_on_first_visit"]
    ordering = ["order", "-created_at"]
    readonly_fields = ["created_at", "updated_at", "video_preview", "thumbnail_preview"]

    fieldsets = (
        ("اطلاعات اصلی", {"fields": ("title", "description", "route_path", "duration", "tags")}),
        (
            "ویدیو",
            {
                "fields": ("video", "video_url", "video_preview"),
                "description": "فقط یکی از فیلدهای ویدیو یا لینک ویدیو را پر کنید",
            },
        ),
        ("تصویر پیش‌نمایش", {"fields": ("thumbnail", "thumbnail_preview")}),
        ("تنظیمات نمایش", {"fields": ("show_on_first_visit", "order", "is_active")}),
        ("زمان‌بندی", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def video_source_type(self, obj):
        source = obj.get_video_source()
        if source:
            if source["type"] == "file":
                return format_html('<span style="color: green;">📁 فایل آپلود شده</span>')
            else:
                return format_html('<span style="color: blue;">🔗 لینک خارجی</span>')
        return format_html('<span style="color: red;">❌ بدون منبع</span>')

    video_source_type.short_description = "نوع منبع"

    def video_preview(self, obj):
        source = obj.get_video_source()
        if source and source["url"]:
            if source["type"] == "file":
                return format_html(
                    '<video width="320" height="240" controls><source src="{}" type="video/mp4"></video>', source["url"]
                )
            else:
                return format_html('<a href="{}" target="_blank">مشاهده ویدیو</a>', source["url"])
        return "-"

    video_preview.short_description = "پیش‌نمایش ویدیو"

    def thumbnail_preview(self, obj):
        if obj.thumbnail and obj.thumbnail.file:
            return format_html('<img src="{}" width="200" />', obj.thumbnail.file.url)
        return "-"

    thumbnail_preview.short_description = "پیش‌نمایش تصویر"

    actions = ["enable_first_visit", "disable_first_visit"]

    @admin.action(description="فعال‌سازی نمایش در اولین بازدید")
    def enable_first_visit(self, request, queryset):
        updated = queryset.update(show_on_first_visit=True)
        self.message_user(request, f"{updated} ویدیو برای نمایش خودکار فعال شد.")

    @admin.action(description="غیرفعال‌سازی نمایش در اولین بازدید")
    def disable_first_visit(self, request, queryset):
        updated = queryset.update(show_on_first_visit=False)
        self.message_user(request, f"{updated} ویدیو از نمایش خودکار غیرفعال شد.")
