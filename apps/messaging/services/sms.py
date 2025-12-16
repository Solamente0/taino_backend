import logging
import random
from abc import ABC, abstractmethod
from typing import List, Any, Dict, Optional

from rest_framework.status import is_success

from django.conf import settings

from base_utils.facades.http import HttpRequestManager

log = logging.getLogger(__name__)


class AbstractSmsManager(ABC):

    @abstractmethod
    def send(self, phone_number: str, message: str, **kwargs):
        raise NotImplemented

    @abstractmethod
    def bulk_send(self, phone_numbers: List[str], messages: List[str], **kwargs):
        raise NotImplemented

    def send_verification_code(self, phone_number: str, code: str, **kwargs):
        return self.send(phone_number, message=code, **kwargs)


class IranSmsManager(AbstractSmsManager):
    BASE_URL = "https://api.sms.ir"
    BULK_SEND_API = f"{BASE_URL}/v1/send/bulk/"
    LINE_API = f"{BASE_URL}/v1/line/"
    VERIFY_API = f"{BASE_URL}/v1/send/verify"
    DEFAULT_PANEL_NUMBER = "30007732001071"
    VERIFICATION_TEMPLATE_ID = settings.VERIFICATION_TEMPLATE_ID

    def __init__(self, api_key: str = None, user_default_number: bool = False):
        if not api_key:
            api_key = settings.SMS_IR_API_KEY

        self.api_key = api_key
        self.user_default_number = user_default_number
        self._headers = {
            "X-API-KEY": self.api_key,
            "ACCEPT": "application/json",
            "Content-Type": "application/json",
        }
        self.http_request_manager = HttpRequestManager(self._headers)
        self.line_number = self.__decide_panel_number()

    def __decide_panel_number(self):
        if not self.user_default_number:
            line_numbers = self.get_line_numbers()
            if not line_numbers:
                raise Exception("SMS.ir is not available")

            return random.choice(line_numbers)
        return self.DEFAULT_PANEL_NUMBER

    def bulk_send(self, phone_numbers: List[str], messages: List[str], **kwargs):
        for message in messages:
            data = {
                "lineNumber": self.line_number,
                "messageText": message,
                "mobiles": phone_numbers,
            }

            res = self.http_request_manager.post(self.BULK_SEND_API, data=data)

    def send_verification_code(self, phone_number: str, code: str, **kwargs):
        data = {
            "mobile": phone_number,
            "templateId": self.VERIFICATION_TEMPLATE_ID,
            "parameters": [
                {"name": "CODE", "value": str(code)},
            ],
        }
        print(f"here 81", flush=True)
        res = self.http_request_manager.post(self.VERIFY_API, data=data)
        print(f"sms sent response:: {res=}", flush=True)
        log.info(f"sms sent response:: {res=}")
        log.info(f"sms sent response:: {res.json()=}")
        if not is_success(res.status_code):
            return self.send(phone_number, code, **kwargs)

    def send_template_sms(self, phone_number: str, parameters: List[Dict[str, Any]], template_id: str, **kwargs) -> bool:
        """
        Send an SMS using SMS.ir's template system

        Args:
            phone_number: Recipient phone number
            parameters: List of parameter dictionaries in format [{"name": "PARAM_NAME", "value": "PARAM_VALUE"}]
            template_id: The SMS.ir template ID

        Returns:
            bool: True if successful, False otherwise
        """
        data = {"mobile": phone_number, "templateId": template_id, "parameters": parameters}

        log.info(f"Sending template SMS to {phone_number} using template ID {template_id} with parameters: {parameters}")

        try:
            res = self.http_request_manager.post(self.VERIFY_API, data=data)

            log.info(f"SMS.ir template response: Status={res.status_code}")

            if is_success(res.status_code):
                response_data = res.json()
                log.info(f"SMS.ir template response data: {response_data}")
                return True
            else:
                log.error(f"SMS.ir template error: {res.text}")
                return False

        except Exception as e:
            log.error(f"Exception sending template SMS: {e}")
            return False

    def send(self, phone_number: str, message: str, **kwargs):
        self.bulk_send([phone_number], [message])

    def get_line_numbers(self) -> List[str]:
        response = self.http_request_manager.get(
            self.LINE_API,
        )
        line_number = response.json().get("data", [])
        return line_number


class TainoSMSHandler:
    @staticmethod
    def send_verification_code(*, dial_code: str, code: str, phone_number: str) -> bool:
        """
        Check the dial_code and send sms with IR or TR
        """
        params = {"code": code, "phone_number": phone_number}
        try:
            ir_sms = IranSmsManager()
            if dial_code == "98":  # todo not hardcode
                ir_sms.send_verification_code(**params)

            return True
        except Exception as e:
            log.info(f"exception {e} occurred in {__file__}!")
            return False

    @staticmethod
    def send_template_code(dial_code: str, phone_number: str, params: List[Dict[str, Any]], template_id: str) -> bool:
        """
        Send an SMS using the SMS.ir template system

        Args:
            dial_code: Country dial code (e.g., "98" for Iran)
            phone_number: Recipient phone number
            params: List of parameter dictionaries [{"name": "PARAM_NAME", "value": "PARAM_VALUE"}]
            template_id: The SMS.ir template ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if dial_code is None or dial_code == "":
                dial_code = "98"

            ir_sms = IranSmsManager()
            if dial_code == "98":  # todo not hardcode
                return ir_sms.send_template_sms(phone_number, params, template_id)
            else:
                log.warning(f"Unsupported dial code: {dial_code}")
                return False

        except Exception as e:
            log.error(f"Exception in send_template_code: {e}")
            return False
