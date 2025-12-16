import logging
from dataclasses import dataclass
from enum import Enum
from typing import Literal, Dict

from django.template.loader import render_to_string
from django.utils.safestring import SafeString

from config.settings import AvailableLanguageChoices
from django.utils.translation import gettext_lazy as _

log = logging.getLogger(__name__)


class TainoDefaultMessageFormats(Enum):
    AUTHENTICATION_SMS_MESSAGE_TEMPLATE = "Your Taino verification code is: %s \n Tainoekalat, your smart assistant."
    EMAIL_VERIFICATION_SUBJECT = _("Subject: Taino Verification Code")
    EMAIL_VERIFICATION_MESSAGE = "Online Vekalat code: %s"


@dataclass
class TainoEmailTemplate:
    REGISTRATION = "registration.html"
    OTP = "otp.html"
    RESET_PASSWORD = "reset-password.html"
    RESET_PASSWORD_CONFIRMATION = "reset-password-confirmation.html"

    # each html file has a context
    CONTEXT_MAP = {
        REGISTRATION: dict(code="code"),
        OTP: dict(code="code"),
        RESET_PASSWORD: dict(code="code", user_fullname="user_fullname"),
        RESET_PASSWORD_CONFIRMATION: dict(code="code", user_fullname="user_fullname"),
    }


class TainoEmailTemplateSwitcherService:

    def render_template(
        self, template_name: str, language: Literal[AvailableLanguageChoices.values], template_context: Dict
    ) -> SafeString:

        if not TainoEmailTemplate.CONTEXT_MAP.get(template_name):
            raise Exception("No context provided by this template")

        if not set(template_context.keys()) == set(TainoEmailTemplate.CONTEXT_MAP[template_name].keys()):
            raise Exception("Provided context does not have all the data")
        rendered_template = render_to_string(f"email/{language}/{template_name}", template_context)
        return rendered_template
