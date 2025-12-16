import logging

from django.contrib.auth import get_user_model
from django.utils import timezone


log = logging.getLogger(__name__)
User = get_user_model()


class DeleteAccountService:
    def __init__(self, user: User, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def change_unique_fields(self):
        self.user.email = "#_" + self.user.email if getattr(self.user, "email", None) else None
        self.user.phone_number = "#_" + self.user.phone_number if getattr(self.user, "phone_number", None) else None
        self.user.save()

    def deactivate_user(self):
        self.user.is_active = False
        self.user.save()

    def delete(self):
        self.change_unique_fields()
        self.deactivate_user()
        try:
            self.user.is_deleted = True
            self.user.deleted_at = timezone.now()
            self.user.save()
        except Exception as e:
            log.error(f"DELETE ACCOUNT ERROR {e} \nFile: {__file__}!")
            pass
