from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.banner.api.v1.serializers import BannerListSerializer
from apps.banner.services.query import BannerQuery
from base_utils.filters import IsActiveFilterBackend
from base_utils.views.mobile import TainoMobileReadOnlyModelViewSet


class BannerViewSet(TainoMobileReadOnlyModelViewSet):
    serializer_class = BannerListSerializer

    filter_backends = [IsActiveFilterBackend, SearchFilter, DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["header_text", "bold_text", "footer_text", "pid", "where_to_place"]
    search_fields = ["header_text", "bold_text", "footer_text", "pid", "where_to_place"]
    ordering_fields = ["created_at", "updated_at", "order"]
    ordering = ["order", "-created_at"]

    def get_queryset(self):
        """
        اگر query param ای location داشته باشیم، فیلتر می‌کنیم
        در غیر این صورت همه بنرهای فعال رو برمی‌گردونیم
        """
        queryset = BannerQuery.get_visible_banners()

        # فیلتر بر اساس location از query params
        location = self.request.query_params.get('location', None)
        if location:
            queryset = BannerQuery.get_banners_by_location(location)

        return queryset

    @action(detail=False, methods=['get'], url_path='by-location/(?P<location>.+)')
    def by_location(self, request, location=None):
        """
        Custom endpoint برای دریافت بنرهای یک لوکیشن خاص

        مثال: /banner/v1/by-location/root/
        مثال: /banner/v1/by-location/dashboard/path/
        """
        queryset = BannerQuery.get_banners_by_location(location)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='root')
    def root_banners(self, request):
        """
        Shortcut endpoint برای دریافت بنرهای صفحه اصلی

        مثال: /banner/v1/root/
        """
        queryset = BannerQuery.get_root_banners()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='locations')
    def available_locations(self, request):
        """
        دریافت لیست تمام لوکیشن‌هایی که بنر دارند

        مثال: /banner/v1/locations/
        """
        locations = BannerQuery.get_available_locations()
        return Response({
            'locations': list(locations)
        })
