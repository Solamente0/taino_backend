from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count
from django.urls import reverse
from django.utils.safestring import mark_safe

from apps.authentication.models import (
    TainoUser,
    UserType,
    UserProfile,
    UserDocument,
    AuthProvider,
    UserDevice,
)

User = get_user_model()


class UserDeviceInline(admin.TabularInline):
    model = UserDevice
    extra = 0
    readonly_fields = ("device_id", "device_name", "user_agent", "ip_address", "last_login")
    can_delete = True
    fields = ("device_id", "device_name", "is_active", "last_login", "ip_address", "user_agent")

    def has_add_permission(self, request, obj=None):
        return False


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    extra = 0
    can_delete = False
    fk_name = "user"  # Specify which ForeignKey to use
    verbose_name = _("پروفایل کاربر")
    verbose_name_plural = _("پروفایل کاربر")

    fieldsets = (
        (
            _("اطلاعات وکیل"),
            {
                "fields": (
                    "license_number",
                    "bar_association",
                    "lawyer_type",
                    "office_phone",
                    "office_address",
                    "office_location",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("اطلاعات شخص حقوقی"),
            {
                "fields": ("legal_entity_name", "legal_entity_id", "legal_entity_phone"),
                "classes": ("collapse",),
            },
        ),
        (
            _("اطلاعات منشی"),
            {
                "fields": ("is_secretary", "lawyer"),
                "classes": ("collapse",),
            },
        ),
        (
            _("آدرس و بایگانی"),
            {
                "fields": ("address", "archive_cabinet"),
                "classes": ("collapse",),
            },
        ),
    )


class UserDocumentInline(admin.TabularInline):
    model = UserDocument
    extra = 0
    readonly_fields = ("file_type", "file_url_display")
    fields = ("file", "file_type", "file_url_display")

    def file_url_display(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">مشاهده فایل</a>', obj.file_url)
        return "-"

    file_url_display.short_description = _("لینک فایل")


@admin.register(TainoUser)
class TainoUserAdmin(BaseUserAdmin):
    list_display = (
        "vekalat_id",
        "get_full_name_display",
        "phone_number",
        "email",
        "role_display",
        "provider_display",
        "is_active",
        "has_premium_account",
        "date_joined",
        "active_devices_count",
    )

    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "is_admin",
        "has_premium_account",
        "is_email_verified",
        "is_phone_number_verified",
        "role",
        "provider",
        "phone_country",
        "country",
        "date_joined",
    )

    search_fields = (
        "vekalat_id",
        "first_name",
        "last_name",
        "phone_number",
        "email",
        "national_code",
    )

    ordering = ("-date_joined",)

    readonly_fields = (
        "vekalat_id",
        "date_joined",
        "last_login",
        "avatar_display",
        "active_devices_count",
        "subscription_status",
    )

    fieldsets = (
        (
            _("اطلاعات اصلی"),
            {
                "fields": (
                    "vekalat_id",
                    "first_name",
                    "last_name",
                    "national_code",
                    "birth_date",
                    "age",
                )
            },
        ),
        (
            _("اطلاعات تماس"),
            {
                "fields": (
                    "phone_number",
                    "phone_country",
                    "email",
                    "is_phone_number_verified",
                    "is_email_verified",
                )
            },
        ),
        (
            _("تنظیمات کاربری"),
            {
                "fields": (
                    "role",
                    "provider",
                    "country",
                    "language",
                    "currency",
                )
            },
        ),
        (
            _("آواتار"),
            {
                "fields": ("avatar", "avatar_display"),
                "classes": ("collapse",),
            },
        ),
        (
            _("دسترسی‌ها و وضعیت"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_admin",
                    "has_premium_account",
                    "subscription_status",
                    "is_subscribe",
                )
            },
        ),
        (
            _("تاریخ‌ها"),
            {
                "fields": ("date_joined", "last_login", "active_devices_count"),
                "classes": ("collapse",),
            },
        ),
        (
            _("رمز عبور"),
            {
                "fields": ("password",),
                "classes": ("collapse",),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "phone_number",
                    "phone_country",
                    "email",
                    "first_name",
                    "last_name",
                    "national_code",
                    "role",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    inlines = [UserProfileInline, UserDeviceInline, UserDocumentInline]

    actions = [
        "activate_users",
        "deactivate_users",
        "grant_premium",
        "revoke_premium",
        "verify_email",
        "verify_phone",
        "deactivate_all_devices",
    ]

    def get_full_name_display(self, obj):
        full_name = obj.get_full_name()
        if full_name:
            return full_name
        return obj.phone_number or obj.email or obj.vekalat_id

    get_full_name_display.short_description = _("نام و نام خانوادگی")

    def role_display(self, obj):
        if obj.role:
            return format_html(
                '<span style="background-color: #{}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
                obj.role.color or "007bff",
                obj.role.name,
            )
        return "-"

    role_display.short_description = _("نقش")

    def provider_display(self, obj):
        if obj.provider:
            url = reverse("admin:barlawyer_bar_change", args=[obj.provider.pk])
            return format_html('<a href="{}">{}</a>', url, obj.provider.name)
        return "-"

    provider_display.short_description = _("کانون ارائه‌دهنده")

    def avatar_display(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 8px;" />', obj.avatar_url
            )
        return "-"

    avatar_display.short_description = _("آواتار")

    def active_devices_count(self, obj):
        active_count = obj.devices.filter(is_active=True).count()
        total_count = obj.devices.count()

        if active_count > 0:
            color = "green"
        else:
            color = "gray"

        return format_html('<span style="color: {}; font-weight: bold;">{} / {}</span>', color, active_count, total_count)

    active_devices_count.short_description = _("دستگاه‌های فعال")

    def subscription_status(self, obj):
        from apps.subscription.services.subscription import SubscriptionService

        has_active = SubscriptionService.has_active_subscription(obj)

        if has_active or obj.has_premium_account:
            return format_html('<span style="color: green; font-weight: bold;">✓ فعال</span>')
        return format_html('<span style="color: gray;">غیرفعال</span>')

    subscription_status.short_description = _("وضعیت اشتراک")

    # Actions
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} کاربر فعال شدند.")

    activate_users.short_description = _("فعال‌سازی کاربران انتخاب شده")

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} کاربر غیرفعال شدند.")

    deactivate_users.short_description = _("غیرفعال‌سازی کاربران انتخاب شده")

    def grant_premium(self, request, queryset):
        updated = queryset.update(has_premium_account=True)
        self.message_user(request, f"اشتراک ویژه به {updated} کاربر اعطا شد.")

    grant_premium.short_description = _("اعطای اشتراک ویژه")

    def revoke_premium(self, request, queryset):
        updated = queryset.update(has_premium_account=False)
        self.message_user(request, f"اشتراک ویژه از {updated} کاربر لغو شد.")

    revoke_premium.short_description = _("لغو اشتراک ویژه")

    def verify_email(self, request, queryset):
        updated = queryset.update(is_email_verified=True)
        self.message_user(request, f"ایمیل {updated} کاربر تایید شد.")

    verify_email.short_description = _("تایید ایمیل")

    def verify_phone(self, request, queryset):
        updated = queryset.update(is_phone_number_verified=True)
        self.message_user(request, f"شماره تلفن {updated} کاربر تایید شد.")

    verify_phone.short_description = _("تایید شماره تلفن")

    def deactivate_all_devices(self, request, queryset):
        total = 0
        for user in queryset:
            count = UserDevice.deactivate_all_user_devices(user)
            total += count
        self.message_user(request, f"{total} دستگاه غیرفعال شدند.")

    deactivate_all_devices.short_description = _("غیرفعال‌سازی همه دستگاه‌ها")


@admin.register(UserType)
class UserTypeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "static_name",
        "color_display",
        "is_active",
        "users_count",
    )

    list_filter = ("is_active",)
    search_fields = ("name", "static_name", "description")
    readonly_fields = ("pid", "users_count")

    fieldsets = (
        (_("اطلاعات اصلی"), {"fields": ("pid", "name", "static_name", "description")}),
        (
            _("ظاهر"),
            {
                "fields": ("color", "icon"),
                "classes": ("collapse",),
            },
        ),
        (_("وضعیت"), {"fields": ("is_active", "users_count")}),
    )

    def color_display(self, obj):
        if obj.color:
            return format_html(
                '<div style="width: 50px; height: 25px; background-color: #{}; border: 1px solid #ddd; border-radius: 3px;"></div>',
                obj.color,
            )
        return "-"

    color_display.short_description = _("رنگ")

    def users_count(self, obj):
        count = obj.users.count()
        return format_html(
            '<a href="{}?role__id__exact={}">{} کاربر</a>', reverse("admin:authentication_tainouser_changelist"), obj.id, count
        )

    users_count.short_description = _("تعداد کاربران")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user_display",
        "role_type",
        "license_number",
        "bar_association",
        "is_secretary",
        "has_archive",
    )

    list_filter = (
        "is_secretary",
        "lawyer_type",
        "user__role",
    )

    search_fields = (
        "user__vekalat_id",
        "user__first_name",
        "user__last_name",
        "user__phone_number",
        "user__email",
        "license_number",
        "bar_association",
        "legal_entity_name",
    )

    readonly_fields = ("pid",)

    # Remove autocomplete_fields that cause issues
    raw_id_fields = ("user", "lawyer")

    fieldsets = (
        (_("کاربر"), {"fields": ("pid", "user")}),
        (
            _("اطلاعات وکیل"),
            {
                "fields": (
                    "license_number",
                    "bar_association",
                    "lawyer_type",
                    "office_phone",
                    "office_address",
                    "office_location",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("اطلاعات شخص حقوقی"),
            {
                "fields": (
                    "legal_entity_name",
                    "legal_entity_id",
                    "legal_entity_phone",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("اطلاعات منشی"),
            {
                "fields": ("is_secretary", "lawyer"),
                "classes": ("collapse",),
            },
        ),
        (
            _("آدرس و بایگانی"),
            {
                "fields": ("address", "archive_cabinet"),
            },
        ),
    )

    def user_display(self, obj):
        url = reverse("admin:authentication_tainouser_change", args=[obj.user.pk])
        return format_html(
            '<a href="{}">{} ({})</a>', url, obj.user.get_full_name() or obj.user.vekalat_id, obj.user.vekalat_id
        )

    user_display.short_description = _("کاربر")

    def role_type(self, obj):
        if obj.user.role:
            return obj.user.role.name
        return "-"

    role_type.short_description = _("نقش کاربر")

    def has_archive(self, obj):
        if obj.archive_cabinet:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')

    has_archive.short_description = _("کمد بایگانی")


@admin.register(UserDocument)
class UserDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "creator_display",
        "file_type",
        "file_display",
        "admin_is_active_display",
    )

    list_filter = ("file_type",)

    search_fields = (
        "creator__vekalat_id",
        "creator__first_name",
        "creator__last_name",
        "creator__phone_number",
    )

    readonly_fields = ("pid", "file_type", "file_url")

    # Use raw_id_fields instead of autocomplete_fields
    raw_id_fields = ("creator", "file")

    fieldsets = (
        (_("اطلاعات اصلی"), {"fields": ("pid", "creator", "file", "file_type", "file_url")}),
        (_("وضعیت"), {"fields": ("admin_is_active",) if hasattr(UserDocument, "admin_is_active") else ()}),
    )

    def admin_is_active_display(self, obj):
        return getattr(obj, "admin_is_active", True)

    admin_is_active_display.short_description = _("فعال")
    admin_is_active_display.boolean = True

    def creator_display(self, obj):
        if obj.creator:
            url = reverse("admin:authentication_tainouser_change", args=[obj.creator.pk])
            return format_html('<a href="{}">{}</a>', url, obj.creator.get_full_name() or obj.creator.vekalat_id)
        return "-"

    creator_display.short_description = _("کاربر")

    def file_display(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">مشاهده فایل</a>', obj.file_url)
        return "-"

    file_display.short_description = _("فایل")


@admin.register(AuthProvider)
class AuthProviderAdmin(admin.ModelAdmin):
    list_display = ("title", "code", "redirect_uri")
    list_filter = ()
    search_fields = ("title", "code")
    readonly_fields = ("pid",)

    fieldsets = ((_("اطلاعات اصلی"), {"fields": ("pid", "title", "code", "redirect_uri")}),)


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = (
        "user_display",
        "device_name",
        "device_id_short",
        "is_active",
        "last_login",
        "ip_address",
    )

    list_filter = (
        "is_active",
        "last_login",
    )

    search_fields = (
        "user__vekalat_id",
        "user__first_name",
        "user__last_name",
        "user__phone_number",
        "device_id",
        "device_name",
        "ip_address",
    )

    readonly_fields = (
        "pid",
        "device_id",
        "user_agent",
        "ip_address",
        "last_login",
    )

    autocomplete_fields = ("user",)

    fieldsets = (
        (_("کاربر و دستگاه"), {"fields": ("pid", "user", "device_id", "device_name")}),
        (_("اطلاعات اتصال"), {"fields": ("user_agent", "ip_address", "is_active")}),
        (
            _("تاریخ‌ها"),
            {
                "fields": ("last_login",),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["activate_devices", "deactivate_devices"]

    def user_display(self, obj):
        url = reverse("admin:authentication_tainouser_change", args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name() or obj.user.vekalat_id)

    user_display.short_description = _("کاربر")

    def device_id_short(self, obj):
        if len(obj.device_id) > 20:
            return obj.device_id[:20] + "..."
        return obj.device_id

    device_id_short.short_description = _("شناسه دستگاه")

    def activate_devices(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} دستگاه فعال شدند.")

    activate_devices.short_description = _("فعال‌سازی دستگاه‌های انتخاب شده")

    def deactivate_devices(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} دستگاه غیرفعال شدند.")

    deactivate_devices.short_description = _("غیرفعال‌سازی دستگاه‌های انتخاب شده")
