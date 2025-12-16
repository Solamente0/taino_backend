from django.db import models
from typing import TypeVar


DjangoModelType = TypeVar("DjangoModelType", bound=models.Model)
