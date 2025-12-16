from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from apps.analyzer.models import AnalyzerLog


@admin.register(AnalyzerLog)
class AnalyzerLogAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ["pid", "user", "ai_type", "created_at"]
    list_filter = ["ai_type", "created_at"]
    search_fields = ["user__email", "prompt", "analysis_text"]
    readonly_fields = ["pid", "created_at", "updated_at"]

    fieldsets = (
        ("Basic Info", {"fields": ("pid", "user", "ai_type")}),
        ("Content", {"fields": ("prompt", "analysis_text")}),
        ("Session Info", {"fields": ("ai_session",)}),
        ("Status", {"fields": ("is_active", "is_deleted", "created_at", "updated_at")}),
    )
