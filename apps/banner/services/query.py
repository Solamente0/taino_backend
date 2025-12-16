from django.db.models import QuerySet
from typing import Optional

from apps.banner.models import Banner
from base_utils.services import AbstractBaseQuery


class BannerQuery(AbstractBaseQuery):

    @staticmethod
    def get_visible_banners(base_queryset: QuerySet[Banner] = None) -> QuerySet[Banner]:
        """دریافت تمام بنرهای فعال"""
        if not base_queryset:
            base_queryset = Banner.objects.all()

        return base_queryset.filter(is_active=True).order_by('order', '-created_at')

    @staticmethod
    def get_banners_by_location(
            location: str,
            base_queryset: QuerySet[Banner] = None
    ) -> QuerySet[Banner]:
        """
        دریافت بنرهای مخصوص یک لوکیشن خاص

        Args:
            location: آدرس صفحه مثل '/dashboard/path' یا 'root' برای صفحه اصلی
            base_queryset: QuerySet پایه (اختیاری)

        Returns:
            QuerySet فیلتر شده بنرها
        """
        if not base_queryset:
            base_queryset = Banner.objects.all()

        # فیلتر بر اساس لوکیشن و فعال بودن
        return (
            base_queryset
            .filter(is_active=True, where_to_place=location)
            .select_related('file')  # برای بهینه‌سازی
            .order_by('order', '-created_at')
        )

    @staticmethod
    def get_root_banners(base_queryset: QuerySet[Banner] = None) -> QuerySet[Banner]:
        """
        دریافت بنرهای صفحه اصلی

        این متد shortcut برای دریافت بنرهای root است
        """
        return BannerQuery.get_banners_by_location('root', base_queryset)

    @staticmethod
    def get_available_locations() -> list[str]:
        """
        دریافت لیست تمام لوکیشن‌هایی که بنر دارند

        Returns:
            لیست آدرس‌های صفحات که بنر فعال دارند
        """
        return (
            Banner.objects
            .filter(is_active=True, where_to_place__isnull=False)
            .values_list('where_to_place', flat=True)
            .distinct()
            .order_by('where_to_place')
        )
