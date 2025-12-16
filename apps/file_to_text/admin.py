# apps/file_to_text/admin.py
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from apps.file_to_text.models import FileToTextLog


@admin.register(FileToTextLog)
class FileToTextLogAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ["pid", "user", "original_filename", "file_type", "coins_used", "character_count", "created_at"]
    list_filter = ["file_type", "created_at", "ai_type"]
    search_fields = ["user__email", "user__phone_number", "original_filename", "extracted_text"]
    readonly_fields = ["pid", "created_at", "updated_at"]

    fieldsets = (
        ("اطلاعات پایه", {
            "fields": ("pid", "user", "ai_type", "coins_used")
        }),
        ("اطلاعات فایل", {
            "fields": ("original_filename", "file_type", "file_size")
        }),
        ("محتوا", {
            "fields": ("extracted_text", "character_count", "word_count")
        }),
        ("وضعیت", {
            "fields": ("is_active", "is_deleted", "created_at", "updated_at")
        }),
    )
