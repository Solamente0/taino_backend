from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.banner.models import Banner


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = [
        "get_thumbnail",
        "pid",
        "where_to_place",
        "banner_type_badge",
        "bold_text",
        "order",
        "is_active_badge",
        "created_at",
    ]

    list_filter = [
        "banner_type",
        "is_active",
        "where_to_place",
        "created_at",
        "updated_at",
    ]

    search_fields = [
        "pid",
        "header_text",
        "bold_text",
        "footer_text",
        "link",
        "where_to_place",
    ]

    readonly_fields = [
        "pid",
        "created_at",
        "updated_at",
        "preview",
    ]

    list_editable = [
        "order",
    ]

    ordering = ["order", "-created_at"]

    list_per_page = 20

    date_hierarchy = "created_at"

    actions = [
        "activate_banners",
        "deactivate_banners",
        "duplicate_banner",
    ]

    fieldsets = (
        (
            _("اطلاعات اصلی"),
            {
                "fields": (
                    "pid",
                    "banner_type",
                    "where_to_place",
                    "order",
                    "is_active",
                    "display_duration",
                )
            },
        ),
        (
            _("محتوای بنر"),
            {
                "fields": (
                    "file",
                    "iframe_code",
                    "iframe_height",
                ),
                "description": "برای بنر تصویری فایل و برای iframe/embed کد مربوطه را وارد کنید.",
            },
        ),
        (
            _("متن‌های بنر"),
            {
                "fields": (
                    "header_text",
                    "bold_text",
                    "footer_text",
                ),
                "classes": ("collapse",),
                "description": "این فیلدها برای بنرهای تصویری استفاده می‌شوند.",
            },
        ),
        (
            _("لینک و دکمه"),
            {
                "fields": (
                    "link_title",
                    "link",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("پیش‌نمایش"),
            {
                "fields": ("preview",),
                "classes": ("collapse",),
            },
        ),
        (
            _("تاریخ‌ها"),
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def get_thumbnail(self, obj):
        """نمایش تصویر کوچک برای بنرهای تصویری"""
        if obj.banner_type == "image" and obj.file:
            try:
                return format_html(
                    '<img src="{}" style="width: 100px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                    obj.file.file.url,
                )
            except:
                return format_html('<span style="color: #999;">بدون تصویر</span>')
        elif obj.banner_type in ["iframe", "embed"]:
            return format_html(
                '<div style="width: 100px; height: 50px; background: #f0f0f0; '
                "border-radius: 4px; display: flex; align-items: center; "
                'justify-content: center; font-size: 10px; color: #666;">'
                "<code>{}</code></div>",
                obj.banner_type.upper(),
            )
        return format_html('<span style="color: #999;">-</span>')

    get_thumbnail.short_description = _("پیش‌نمایش")

    def banner_type_badge(self, obj):
        """نمایش نوع بنر با رنگ‌بندی"""
        colors = {
            "image": "#10b981",
            "iframe": "#3b82f6",
            "embed": "#8b5cf6",
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            colors.get(obj.banner_type, "#6b7280"),
            obj.get_banner_type_display(),
        )

    banner_type_badge.short_description = _("نوع بنر")
    banner_type_badge.admin_order_field = "banner_type"

    def is_active_badge(self, obj):
        """نمایش وضعیت فعال/غیرفعال"""
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
    is_active_badge.admin_order_field = "is_active"

    def preview(self, obj):
        """پیش‌نمایش کامل بنر"""
        if obj.banner_type == "image" and obj.file:
            try:
                preview_html = f"""
                <div style="max-width: 800px; border: 2px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                    <img src="{obj.file.file.url}" style="width: 100%; height: auto; display: block;" />
                """

                # اضافه کردن متن‌ها اگر وجود داشته باشند
                if obj.header_text or obj.bold_text or obj.footer_text:
                    preview_html += '<div style="padding: 15px; background: #f9fafb;">'
                    if obj.header_text:
                        preview_html += (
                            f'<div style="font-size: 12px; color: #6b7280; margin-bottom: 5px;">{obj.header_text}</div>'
                        )
                    if obj.bold_text:
                        preview_html += f'<div style="font-size: 18px; font-weight: bold; color: #111827; margin-bottom: 5px;">{obj.bold_text}</div>'
                    if obj.footer_text:
                        preview_html += (
                            f'<div style="font-size: 12px; color: #6b7280; margin-bottom: 5px;">{obj.footer_text}</div>'
                        )
                    if obj.link_title and obj.link:
                        preview_html += f'<div style="margin-top: 10px;"><a href="{obj.link}" target="_blank" style="color: #3b82f6; text-decoration: none; font-weight: 500;">{obj.link_title} →</a></div>'
                    preview_html += "</div>"

                preview_html += "</div>"

                return format_html(preview_html)
            except:
                return format_html('<p style="color: #ef4444;">خطا در نمایش پیش‌نمایش</p>')

        elif obj.banner_type in ["iframe", "embed"] and obj.iframe_code:
            return format_html(
                '<div style="max-width: 800px; border: 2px solid #e5e7eb; border-radius: 8px; overflow: hidden;">'
                '<div style="background: #f9fafb; padding: 10px; border-bottom: 1px solid #e5e7eb;">'
                "<strong>کد {}:</strong>"
                "</div>"
                '<div style="padding: 15px; background: #fff;">'
                '<pre style="background: #f3f4f6; padding: 15px; border-radius: 4px; overflow-x: auto; font-size: 12px;">{}</pre>'
                "</div>"
                "</div>",
                obj.get_banner_type_display(),
                obj.iframe_code[:500] + ("..." if len(obj.iframe_code) > 500 else ""),
            )

        return format_html('<p style="color: #6b7280;">پیش‌نمایشی موجود نیست</p>')

    preview.short_description = _("پیش‌نمایش کامل")

    # Actions
    @admin.action(description=_("فعال کردن بنرهای انتخاب شده"))
    def activate_banners(self, request: HttpRequest, queryset: QuerySet):
        """فعال کردن بنرهای انتخاب شده"""
        updated = queryset.update(is_active=True)
        self.message_user(request, _(f"{updated} بنر فعال شد."), level="success")

    @admin.action(description=_("غیرفعال کردن بنرهای انتخاب شده"))
    def deactivate_banners(self, request: HttpRequest, queryset: QuerySet):
        """غیرفعال کردن بنرهای انتخاب شده"""
        updated = queryset.update(is_active=False)
        self.message_user(request, _(f"{updated} بنر غیرفعال شد."), level="warning")

    @admin.action(description=_("کپی کردن بنرهای انتخاب شده"))
    def duplicate_banner(self, request: HttpRequest, queryset: QuerySet):
        """ایجاد کپی از بنرهای انتخاب شده"""
        count = 0
        for banner in queryset:
            banner.pk = None
            banner.pid = None
            banner.is_active = False
            banner.order = banner.order + 100
            banner.save()
            count += 1

        self.message_user(request, _(f"{count} بنر کپی شد (غیرفعال)."), level="success")

    def get_queryset(self, request: HttpRequest):
        """بهینه‌سازی query با select_related"""
        queryset = super().get_queryset(request)
        return queryset.select_related("file")

    def save_model(self, request: HttpRequest, obj: Banner, form, change: bool):
        """اعتبارسنجی اضافی قبل از ذخیره"""
        # چک کردن اینکه برای تایپ image فایل داشته باشیم
        if obj.banner_type == "image" and not obj.file:
            self.message_user(request, _("برای بنر تصویری، آپلود فایل الزامی است."), level="error")
            return

        # چک کردن اینکه برای تایپ iframe/embed کد داشته باشیم
        if obj.banner_type in ["iframe", "embed"] and not obj.iframe_code:
            self.message_user(
                request, _(f"برای بنر {obj.get_banner_type_display()}، وارد کردن کد الزامی است."), level="error"
            )
            return

        super().save_model(request, obj, form, change)

    class Media:
        css = {"all": ("admin/css/banner_admin.css",)}  # اختیاری برای استایل‌های سفارشی
        js = ("admin/js/banner_admin.js",)  # اختیاری برای جاوااسکریپت سفارشی
