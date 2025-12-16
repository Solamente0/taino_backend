import logging

from django.contrib.auth import get_user_model
from django.db.models import Q

from base_utils.services import AbstractBaseQuery

User = get_user_model()
log = logging.getLogger(__name__)


class UserQuery(AbstractBaseQuery):
    @staticmethod
    def get_user_by_email(*, email: str) -> User | None:
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_user_by_username(*, username: str) -> User | None:
        """
        Get user with this username as phone_number or email

        Return
        ------
            user, does_exist: tuple[User | None, bool]
        """

        queryset = User.objects.filter(Q(phone_number=username) | Q(email=username) | Q(pid=username))
        if queryset:
            user = queryset[0]
        else:
            user = None

        return user
