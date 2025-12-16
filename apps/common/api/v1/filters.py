import django_filters

from apps.common.models import FrequentlyAskedQuestion, TermsOfUse, ServiceItem, TutorialVideo, ServiceCategory


class FrequentlyAskedQuestionFilter(django_filters.FilterSet):
    class Meta:
        model = FrequentlyAskedQuestion
        fields = {
            "question": ["icontains"],
            "created_at": ["gte", "lte"],
            "updated_at": ["gte", "lte"],
        }


class TermsOfUseFilter(django_filters.FilterSet):
    class Meta:
        model = TermsOfUse
        fields = {
            "title": ["icontains"],
            "created_at": ["gte", "lte"],
            "updated_at": ["gte", "lte"],
        }


class ServiceItemFilter(django_filters.FilterSet):
    class Meta:
        model = ServiceItem
        fields = {
            "is_active": ["exact"],
            "soon": ["exact"],
            "static_name": ["exact", "icontains"],
            "name": ["icontains"],
            "order": ["exact", "gte", "lte"],
            "created_at": ["gte", "lte"],
            "updated_at": ["gte", "lte"],
        }


class TutorialVideoFilter(django_filters.FilterSet):
    route_path = django_filters.CharFilter(lookup_expr="icontains")
    tags = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = TutorialVideo
        fields = {
            "is_active": ["exact"],
            "route_path": ["exact", "icontains"],
            "title": ["icontains"],
            "show_on_first_visit": ["exact"],
            "created_at": ["gte", "lte"],
            "updated_at": ["gte", "lte"],
        }


class ServiceCategoryFilter(django_filters.FilterSet):
    class Meta:
        model = ServiceCategory
        fields = {
            "is_active": ["exact"],
            "static_name": ["exact", "icontains"],
            "name": ["icontains"],
            "order": ["exact", "gte", "lte"],
            "created_at": ["gte", "lte"],
            "updated_at": ["gte", "lte"],
        }
