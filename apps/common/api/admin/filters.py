import django_filters
from django_filters.rest_framework.backends import DjangoFilterBackend

from apps.common.models import (
    FrequentlyAskedQuestion,
    TermsOfUse,
    ContactUs,
    Newsletter,
    ServiceItem,
    AboutUs,
    AboutUsTeamMember,
    TutorialVideo, ServiceCategory,
)


class FrequentlyAskedQuestionAdminFilter(django_filters.FilterSet):
    class Meta:
        model = FrequentlyAskedQuestion
        fields = {
            "is_active": ["exact"],
            "order": ["exact", "gte", "lte"],
            "created_at": ["gte", "lte"],
            "updated_at": ["gte", "lte"],
        }


class TermsOfUseAdminFilter(django_filters.FilterSet):
    class Meta:
        model = TermsOfUse
        fields = {
            "is_active": ["exact"],
            "order": ["exact", "gte", "lte"],
            "created_at": ["gte", "lte"],
            "updated_at": ["gte", "lte"],
        }


class ContactUsAdminFilter(django_filters.FilterSet):
    class Meta:
        model = ContactUs
        fields = {
            "is_read": ["exact"],
            "created_at": ["gte", "lte"],
            "name": ["icontains"],
            "email": ["icontains"],
            "subject": ["icontains"],
        }


class NewsletterAdminFilter(django_filters.FilterSet):
    class Meta:
        model = Newsletter
        fields = {
            "is_active": ["exact"],
            "created_at": ["gte", "lte"],
            "email": ["icontains"],
        }


class ServiceItemAdminFilter(django_filters.FilterSet):
    class Meta:
        model = ServiceItem
        fields = {
            "is_active": ["exact"],
            "static_name": ["exact", "icontains"],
            "name": ["icontains"],
            "soon": ["exact"],
            "order": ["exact", "gte", "lte"],
            "created_at": ["gte", "lte"],
            "updated_at": ["gte", "lte"],
        }


class AboutUsAdminFilter(DjangoFilterBackend):
    class Meta:
        model = AboutUs
        fields = {
            "is_active": ["exact"],
            "created_at": ["gte", "lte"],
            "updated_at": ["gte", "lte"],
        }


class AboutUsTeamMemberAdminFilter(DjangoFilterBackend):
    class Meta:
        model = AboutUsTeamMember
        fields = {
            "about_us": ["exact"],
            "is_active": ["exact"],
            "full_name": ["icontains"],
            "job_title": ["icontains"],
            "order": ["exact", "gte", "lte"],
            "created_at": ["gte", "lte"],
            "updated_at": ["gte", "lte"],
        }


class TutorialVideoAdminFilter(django_filters.FilterSet):
    route_path = django_filters.CharFilter(lookup_expr="icontains")
    tags = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = TutorialVideo
        fields = {
            "is_active": ["exact"],
            "route_path": ["exact", "icontains"],
            "title": ["icontains"],
            "show_on_first_visit": ["exact"],
            "order": ["exact", "gte", "lte"],
            "created_at": ["gte", "lte"],
            "updated_at": ["gte", "lte"],
        }


class ServiceCategoryAdminFilter(django_filters.FilterSet):
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
