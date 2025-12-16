import django_filters
from django.contrib.auth import get_user_model

User = get_user_model()


class TainoUserFilter(django_filters.FilterSet):
    class Meta:
        model = User
        fields = ("id", "email", "phone_number", "vekalat_id")
