from django.core.paginator import InvalidPage
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination


class SafePageNumberPagination(PageNumberPagination):
    """
    Default DRF PageNumberPagination raises 404 when has no data, We needed it to return empty list instead, LimitOffsetPagination class
    """

    def __init__(self, page_size):
        self.page_size = page_size

    def get_count(self):
        try:
            return self.page.paginator.count
        except Exception as e:
            return 0

    def get_next_link(self):
        try:
            return super().get_next_link()
        except Exception as e:
            return None

    def get_previous_link(self):
        try:
            return super().get_previous_link()
        except Exception as e:
            return None

    def paginate_queryset(self, queryset, request, view=None):
        try:
            return super().paginate_queryset(queryset, request, view)
        except (InvalidPage, NotFound) as e:
            return []

    def get_page_number(self, request, paginator):
        request_page_number = request.query_params.get(self.page_query_param)
        if isinstance(request_page_number, str):
            request_page_number = int(request_page_number)

        page_number = request_page_number or 1
        if page_number in self.last_page_strings:
            page_number = paginator.num_pages
        return page_number
