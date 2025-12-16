from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException


class InvalidUsernameOrPassword(APIException):
    status_code = 400
    default_detail = _("No such user with the given credentials")
    default_code = "invalid_username_or_password"


class Required(APIException):
    status_code = 400
    default_detail = _("This is required")
    default_code = "required"

    def __init__(self, field, detail=None, code=None):
        if detail is None:
            detail = force_str(self.default_detail).format(field=field)
        super().__init__(detail, code)
