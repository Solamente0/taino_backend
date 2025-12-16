import logging
from typing import Any, Type

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import MultipleObjectsReturned
from django.db.models import QuerySet

from base_utils.types import DjangoModelType

log = logging.getLogger(__name__)


def get_or_create(
    model: DjangoModelType | Type[ContentType] | Any, filters: dict[str, Any], orders: list[str] = None, latest: bool = False
) -> QuerySet | bool | Any:
    if orders is None:
        orders = ["-id"]
    try:
        objs = model.objects.filter(**filters).order_by(*orders)
        if not objs.exists():
            # TODO: we must create the object here!
            return None
        if latest:
            return objs.last()
        return objs.first()
    except Exception as e:
        log.info(f"GET_OR_CREATE EXCEPTION {e=} in {__file__} in LINE15")
        return None
