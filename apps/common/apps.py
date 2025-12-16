"""
Auto admin registration system for Django.
This module registers all models to the Django admin site automatically
with appropriate admin classes based on model characteristics.
"""

import jdatetime
from django.apps import AppConfig, apps
from django.contrib import admin as django_admin
from django.db import models
from django.urls import reverse
from django.utils.html import format_html
import jdatetime
from django.contrib import admin

import jdatetime
from django.contrib import admin

class JalaliDateFieldListFilter(admin.DateFieldListFilter):
    """فیلتر تاریخ شمسی برای لیست Admin"""

    def __init__(self, field, request, params, model, model_admin, field_path):
        super().__init__(field, request, params, model, model_admin, field_path)

        # تبدیل تاریخ‌های فیلتر به شمسی
        now = jdatetime.datetime.now()

        # ساخت فیلترهای جدید بصورت tuple
        self.links = self.links[:1] + (
            ('امروز', {
                self.lookup_kwarg_since: str(now.date()),
                self.lookup_kwarg_until: str(now.date() + jdatetime.timedelta(days=1)),
            }),
            ('این هفته', {
                self.lookup_kwarg_since: str(now.date() - jdatetime.timedelta(days=now.weekday())),
            }),
            ('این ماه', {
                self.lookup_kwarg_since: str(now.replace(day=1).date()),
            }),
        )

class UserAdminWithHardDelete(django_admin.ModelAdmin):
    def delete_model(self, request, obj):
        # Call hard_delete instead of delete
        obj.hard_delete()

    def delete_queryset(self, request, queryset):
        # For bulk deletions
        queryset.hard_delete()


class BaseAdminMixin:
    """Base mixin providing common admin functionality."""

    def change_button(self, obj):
        """Generate a 'Change' button for the object."""
        url = reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change", args=[obj.pk])
        return format_html('<a class="btn btn-primary" href="{}">Change</a>', url)

    def delete_button(self, obj):
        """Generate a 'Delete' button for the object."""
        url = reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_delete", args=[obj.pk])
        return format_html('<a class="btn btn-danger" href="{}">Delete</a>', url)


class ListConfigurationMixin(BaseAdminMixin):
    """Mixin to configure list display, filters, and pagination."""

    # Default settings that can be overridden in child classes
    exclude_from_list_display = []
    exclude_from_list_filter = ["id"]
    extra_list_display = []
    list_per_page = 25

    # Field types that can be used as filters
    filterable_field_types = (
        models.ForeignKey,
        models.BooleanField,
        models.DateField,
        models.DateTimeField,
        models.DecimalField,
        models.IntegerField,
        models.CharField,
        models.EmailField,
    )

    def __init__(self, model, admin_site):
        """
        Dynamically determine list_display and list_filter based on model fields.
        """
        # Set list_display based on model fields excluding specific fields
        self.list_display = [
            field.name for field in model._meta.fields if field.name not in self.exclude_from_list_display
        ] + self.extra_list_display

        # Set list_filter based on specific field types
        self.list_filter = [
            field.name
            for field in model._meta.fields
            if isinstance(field, self.filterable_field_types) and field.name not in self.exclude_from_list_filter
        ]

        # Call parent initializer
        super().__init__(model, admin_site)


class SingletonModelMixin:
    """
    Admin mixin for singleton models that should only have one instance.
    Prevents deletion and disables adding if an instance already exists.
    """

    def has_delete_permission(self, request, obj=None):
        """Disable deletion permission."""
        return False

    def has_add_permission(self, request):
        """Only allow adding if no instance exists."""
        return not self.model.objects.exists()


class CommonConfig(AppConfig):
    """App config that automatically registers models with the admin site."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.common"  # Change this to your app name
    verbose_name = "عمومی"

    def ready(self):
        """
        When Django starts, register all models with appropriate admin classes.
        """
        # Import admin classes only when the app is ready to avoid import issues

        django_admin.site.site_header = "مدیریت سایت"  # "Site Administration" in Persian
        django_admin.site.site_title = "پنل مدیریت"  # "Admin Panel" in Persian
        django_admin.site.index_title = "به پنل مدیریت خوش آمدید"  # "Welcome to Admin Panel" in Persian

        from import_export.admin import ImportExportModelAdmin
        from django.contrib.auth import get_user_model

        User = get_user_model()
        # Get all models from all installed apps
        all_models = apps.get_models()

        # Define model-specific overrides
        singleton_models = ["LimitNumber"]  # Models that should only have one instance
        hard_delete_models = [User._meta.model_name]  # Models that should be hard deleted
        # Loop through all models and register each with an appropriate admin class
        for model in all_models:
            # Determine which admin class to use
            if model.__name__ in singleton_models:
                admin_class = type(
                    f"{model.__name__}Admin",
                    (
                        ImportExportModelAdmin,
                        ListConfigurationMixin,
                        SingletonModelMixin,
                        django_admin.ModelAdmin,
                    ),
                    {},
                )
            elif model == User:
                # Special case for User model to enable hard delete
                admin_class = type(
                    f"{model.__name__}Admin",
                    (
                        ImportExportModelAdmin,
                        ListConfigurationMixin,
                        UserAdminWithHardDelete,
                    ),
                    {},
                )
            # elif issubclass(model, TranslatableModel):
            #     admin_class = type(
            #         f"{model.__name__}Admin",
            #         (
            #             ImportExportModelAdmin,
            #             ListConfigurationMixin,
            #             django_admin.ModelAdmin,
            #         ),
            #         {}
            #     )
            else:
                admin_class = type(
                    f"{model.__name__}Admin",
                    (
                        ImportExportModelAdmin,
                        ListConfigurationMixin,
                        django_admin.ModelAdmin,
                    ),
                    {},
                )

            # Try to register the model, ignoring if already registered
            try:
                django_admin.site.register(model, admin_class)
            except django_admin.sites.AlreadyRegistered:
                pass  # Model is already registered, skip it
