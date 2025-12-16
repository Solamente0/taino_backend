from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.landing.models import (
    HeroSection,
    Feature,
    Testimonial,
    FAQ,
    Pricing,
    Team,
    HowItWorks,
    Statistic,
    BlogPost,
    ContactMessage,
    Newsletter,
    AppScreenshot,
)


@admin.register(HeroSection)
class HeroSectionAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "is_active_badge",
        "order",
        "created_at",
    ]

    list_filter = [
        "is_active",
        "created_at",
    ]

    search_fields = [
        "title",
        "subtitle",
        "description",
    ]

    list_editable = ["order"]

    readonly_fields = [
        "pid",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (_("اطلاعات اصلی"), {
            "fields": (
                "pid",
                "title",
                "subtitle",
                "description",
                "is_active",
                "order",
            )
        }),
        (_("دکمه‌های اقدام"), {
            "fields": (
                "cta_primary_text",
                "cta_primary_link",
                "cta_secondary_text",
                "cta_secondary_link",
            )
        }),
        (_("رسانه"), {
            "fields": (
                "background_image",
                "video_url",
            )
        }),
        (_("تاریخ‌ها"), {
            "fields": (
                "created_at",
                "updated_at",
            ),
            "classes": ("collapse",)
        }),
    )

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: bold;">✓ فعال</span>'
            )
        return format_html(
            '<span style="background-color: #ef4444; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">✗ غیرفعال</span>'
        )

    is_active_badge.short_description = _("وضعیت")


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "icon",
        "is_active_badge",
        "order",
        "created_at",
    ]

    list_filter = [
        "is_active",
        "created_at",
    ]

    search_fields = [
        "title",
        "description",
    ]

    list_editable = ["order"]

    readonly_fields = [
        "pid",
        "created_at",
        "updated_at",
    ]

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: bold;">✓ فعال</span>'
            )
        return format_html(
            '<span style="background-color: #ef4444; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">✗ غیرفعال</span>'
        )

    is_active_badge.short_description = _("وضعیت")


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "role",
        "rating_stars",
        "is_active_badge",
        "order",
        "created_at",
    ]

    list_filter = [
        "rating",
        "is_active",
        "created_at",
    ]

    search_fields = [
        "name",
        "role",
        "content",
    ]

    list_editable = ["order"]

    readonly_fields = [
        "pid",
        "created_at",
        "updated_at",
    ]

    def rating_stars(self, obj):
        stars = "★" * obj.rating + "☆" * (5 - obj.rating)
        return format_html(
            '<span style="color: #f59e0b; font-size: 14px;">{}</span>',
            stars
        )

    rating_stars.short_description = _("امتیاز")

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: bold;">✓ فعال</span>'
            )
        return format_html(
            '<span style="background-color: #ef4444; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">✗ غیرفعال</span>'
        )

    is_active_badge.short_description = _("وضعیت")


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = [
        "question",
        "category",
        "is_active_badge",
        "order",
        "created_at",
    ]

    list_filter = [
        "category",
        "is_active",
        "created_at",
    ]

    search_fields = [
        "question",
        "answer",
    ]

    list_editable = ["order"]

    readonly_fields = [
        "pid",
        "created_at",
        "updated_at",
    ]

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: bold;">✓ فعال</span>'
            )
        return format_html(
            '<span style="background-color: #ef4444; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">✗ غیرفعال</span>'
        )

    is_active_badge.short_description = _("وضعیت")


@admin.register(Pricing)
class PricingAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "price_display",
        "is_popular_badge",
        "is_active_badge",
        "order",
        "created_at",
    ]

    list_filter = [
        "is_popular",
        "is_active",
        "created_at",
    ]

    search_fields = [
        "name",
        "description",
    ]

    list_editable = ["order"]

    readonly_fields = [
        "pid",
        "created_at",
        "updated_at",
    ]

    def price_display(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #3b82f6;">{:,} تومان / {}</span>',
            obj.price,
            obj.price_period
        )

    price_display.short_description = _("قیمت")

    def is_popular_badge(self, obj):
        if obj.is_popular:
            return format_html(
                '<span style="background-color: #8b5cf6; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: bold;">⭐ پرطرفدار</span>'
            )
        return "-"

    is_popular_badge.short_description = _("پرطرفدار")

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: bold;">✓ فعال</span>'
            )
        return format_html(
            '<span style="background-color: #ef4444; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">✗ غیرفعال</span>'
        )

    is_active_badge.short_description = _("وضعیت")


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = [
        "get_avatar",
        "name",
        "role",
        "email",
        "is_active_badge",
        "order",
    ]

    list_filter = [
        "is_active",
        "created_at",
    ]

    search_fields = [
        "name",
        "role",
        "email",
    ]

    list_editable = ["order"]

    readonly_fields = [
        "pid",
        "created_at",
        "updated_at",
    ]

    def get_avatar(self, obj):
        if obj.avatar and hasattr(obj.avatar, 'file'):
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover;" />',
                obj.avatar.file.url
            )
        return format_html('<span style="color: #999;">بدون تصویر</span>')

    get_avatar.short_description = _("تصویر")

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: bold;">✓ فعال</span>'
            )
        return format_html(
            '<span style="background-color: #ef4444; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">✗ غیرفعال</span>'
        )

    is_active_badge.short_description = _("وضعیت")


@admin.register(HowItWorks)
class HowItWorksAdmin(admin.ModelAdmin):
    list_display = [
        "step_number",
        "title",
        "is_active_badge",
        "order",
        "created_at",
    ]

    list_filter = [
        "is_active",
        "created_at",
    ]

    search_fields = [
        "title",
        "description",
    ]

    list_editable = ["order"]

    readonly_fields = [
        "pid",
        "created_at",
        "updated_at",
    ]

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: bold;">✓ فعال</span>'
            )
        return format_html(
            '<span style="background-color: #ef4444; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">✗ غیرفعال</span>'
        )

    is_active_badge.short_description = _("وضعیت")


@admin.register(Statistic)
class StatisticAdmin(admin.ModelAdmin):
    list_display = [
        "label",
        "value_display",
        "is_active_badge",
        "order",
    ]

    list_filter = [
        "is_active",
        "created_at",
    ]

    search_fields = [
        "label",
        "value",
    ]

    list_editable = ["order"]

    readonly_fields = [
        "pid",
        "created_at",
        "updated_at",
    ]

    def value_display(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #3b82f6; font-size: 16px;">{}{}</span>',
            obj.value,
            obj.suffix
        )

    value_display.short_description = _("مقدار")

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: bold;">✓ فعال</span>'
            )
        return format_html(
            '<span style="background-color: #ef4444; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">✗ غیرفعال</span>'
        )

    is_active_badge.short_description = _("وضعیت")


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = [
        "get_featured_image",
        "title",
        "author",
        "category",
        "views_count",
        "reading_time",
        "is_active_badge",
        "published_at",
    ]

    list_filter = [
        "category",
        "is_active",
        "published_at",
        "created_at",
    ]

    search_fields = [
        "title",
        "excerpt",
        "content",
    ]

    readonly_fields = [
        "pid",
        "views_count",
        "created_at",
        "updated_at",
    ]

    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        (_("اطلاعات اصلی"), {
            "fields": (
                "pid",
                "title",
                "slug",
                "author",
                "category",
                "tags",
                "is_active",
            )
        }),
        (_("محتوا"), {
            "fields": (
                "excerpt",
                "content",
                "featured_image",
                "reading_time",
            )
        }),
        (_("انتشار"), {
            "fields": (
                "published_at",
                "views_count",
            )
        }),
        (_("تاریخ‌ها"), {
            "fields": (
                "created_at",
                "updated_at",
            ),
            "classes": ("collapse",)
        }),
    )

    def get_featured_image(self, obj):
        if obj.featured_image and hasattr(obj.featured_image, 'file'):
            return format_html(
                '<img src="{}" style="width: 100px; height: 60px; object-fit: cover; border-radius: 4px;" />',
                obj.featured_image.file.url
            )
        return format_html('<span style="color: #999;">بدون تصویر</span>')

    get_featured_image.short_description = _("تصویر شاخص")

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: bold;">✓ فعال</span>'
            )
        return format_html(
            '<span style="background-color: #ef4444; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">✗ غیرفعال</span>'
        )

    is_active_badge.short_description = _("وضعیت")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "email",
        "subject",
        "is_read_badge",
        "created_at",
    ]

    list_filter = [
        "is_read",
        "created_at",
    ]

    search_fields = [
        "name",
        "email",
        "subject",
        "message",
    ]

    readonly_fields = [
        "pid",
        "created_at",
        "name",
        "email",
        "phone",
        "subject",
        "message",
    ]

    actions = ["mark_as_read", "mark_as_unread"]

    def is_read_badge(self, obj):
        if obj.is_read:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: bold;">✓ خوانده شده</span>'
            )
        return format_html(
            '<span style="background-color: #f59e0b; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">! خوانده نشده</span>'
        )

    is_read_badge.short_description = _("وضعیت")

    @admin.action(description=_("علامت‌گذاری به عنوان خوانده شده"))
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, _(f"{updated} پیام به عنوان خوانده شده علامت‌گذاری شد."))

    @admin.action(description=_("علامت‌گذاری به عنوان خوانده نشده"))
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, _(f"{updated} پیام به عنوان خوانده نشده علامت‌گذاری شد."))


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "is_subscribed_badge",
        "created_at",
        "unsubscribed_at",
    ]

    list_filter = [
        "is_subscribed",
        "created_at",
    ]

    search_fields = [
        "email",
    ]

    readonly_fields = [
        "pid",
        "created_at",
    ]

    def is_subscribed_badge(self, obj):
        if obj.is_subscribed:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: bold;">✓ مشترک</span>'
            )
        return format_html(
            '<span style="background-color: #ef4444; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">✗ لغو اشتراک</span>'
        )

    is_subscribed_badge.short_description = _("وضعیت")


@admin.register(AppScreenshot)
class AppScreenshotAdmin(admin.ModelAdmin):
    list_display = [
        "get_thumbnail",
        "title",
        "is_active_badge",
        "order",
        "created_at",
    ]

    list_filter = [
        "is_active",
        "created_at",
    ]

    search_fields = [
        "title",
        "description",
    ]

    list_editable = ["order"]

    readonly_fields = [
        "pid",
        "created_at",
        "updated_at",
    ]

    def get_thumbnail(self, obj):
        if obj.image and hasattr(obj.image, 'file'):
            return format_html(
                '<img src="{}" style="width: 60px; height: 100px; object-fit: cover; border-radius: 4px;" />',
                obj.image.file.url
            )
        return format_html('<span style="color: #999;">بدون تصویر</span>')

    get_thumbnail.short_description = _("تصویر")

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: bold;">✓ فعال</span>'
            )
        return format_html(
            '<span style="background-color: #ef4444; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">✗ غیرفعال</span>'
        )

    is_active_badge.short_description = _("وضعیت")
