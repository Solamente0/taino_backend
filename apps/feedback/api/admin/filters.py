from django_filters.filterset import FilterSet
from django_filters.rest_framework import filters

from apps.feedback.models import FeedBack


class FeedbackFilter(FilterSet):
    feedback_type = filters.ChoiceFilter(choices=FeedBack.FeedbackTypes.choices, lookup_expr="exact")
    status = filters.ChoiceFilter(choices=FeedBack.FeedbackStatus.choices, lookup_expr="exact")
    created_at = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = FeedBack
        fields = [
            "feedback_type",
            "status",
            "created_at",
        ]
