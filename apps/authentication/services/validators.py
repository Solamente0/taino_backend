import re

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _

from apps.authentication.services.query import UserQuery
from apps.authentication.services.regex import PHONE_NUMBER2

User = get_user_model()


def number_validator(password):
    regex = re.compile("[0-9]")
    if regex.search(password) is None:
        raise ValidationError(_("Password must include numbers"), code="password_must_include_number")


def letter_validator(password):
    regex = re.compile("[a-zA-Z]")
    if regex.search(password) is None:
        raise ValidationError(_("Password must include letter"), code="password_must_include_letter")


def special_char_validator(password):
    regex = re.compile("[@_!#$%^&*()<>?/\|}{~:]")
    if regex.search(password) is None:
        raise ValidationError(
            _("password must include special char"),
            code="password_must_include_special_char",
        )


def concat_phone_number(username: str, country) -> str:
    try:
        if re.match(PHONE_NUMBER2, username):
            return country.dial_code + username if not username.startswith(country.dial_code) else username
        return username

    except Exception as e:
        return username


def check_username(username: str) -> str | None:
    try:
        validate_email(username)
        return username  # It's a valid email, so return it
    except Exception as e:
        pass

    if re.match(PHONE_NUMBER2, username):
        return username  #
    else:
        return None


def check_and_repair_username(username: str, country) -> str | None:
    username = check_username(username=username)
    return concat_phone_number(username, country)


def get_and_validate_username(username: str, country) -> User:
    username = check_and_repair_username(username, country)
    return UserQuery.get_user_by_username(username=username)
