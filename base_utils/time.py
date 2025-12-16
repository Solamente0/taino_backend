from datetime import datetime
from typing import Any

import pytz
from django.utils import timezone


def get_today_date_filters() -> tuple[datetime.date, dict[str, Any]]:
    today = timezone.now().date()
    f = dict(created_at__year=today.year, created_at__month=today.month, created_at__day=today.day)
    return today, f


def filter_by_today(queryset, field_name: str):
    today = get_today_date_filters()[0]
    filter_args = {f"{field_name}__year": today.year, f"{field_name}__month": today.month, f"{field_name}__day": today.day}
    return queryset.filter(**filter_args)


def ctainoert_to_tehran_time(datetime_):
    """
    Ctainoerts a datetime object to Tehran timezone (UTC+3:30).

    Args:
        datetime_ (datetime): A datetime object (assumed to be in UTC if timezone-naive).

    Returns:
        datetime: The datetime object in Tehran timezone.
    """
    # Ensure the input datetime is timezone-aware (assume UTC if naive)
    dt = datetime.fromisoformat(datetime_) if isinstance(datetime_, str) else datetime_
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.timezone("UTC"))

    # Ctainoert to Tehran timezone
    tehran_tz = pytz.timezone("Asia/Tehran")
    dt_tehran = dt.astimezone(tehran_tz)

    return dt_tehran
