# apps/payment/services/ipg/zarinpal.py - updated to use ZarinpalPaymentConfig
import json
import logging
import requests
from django.conf import settings
from typing import Dict, Any, Optional, Tuple

from apps.payment.models import ZarinpalPaymentConfig

logger = logging.getLogger(__name__)


class ZarinpalService:
    """Service for interacting with Zarinpal payment gateway"""

    # API endpoints - updated with more recent API URLs
    SANDBOX_API_REQUEST = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
    MAIN_API_REQUEST = "https://api.zarinpal.com/pg/v4/payment/request.json"

    SANDBOX_API_VERIFY = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
    MAIN_API_VERIFY = "https://api.zarinpal.com/pg/v4/payment/verify.json"

    SANDBOX_PAYMENT_GATEWAY = "https://sandbox.zarinpal.com/pg/StartPay/{authority}"
    MAIN_PAYMENT_GATEWAY = "https://www.zarinpal.com/pg/StartPay/{authority}"

    def __init__(self):
        """Initialize the service with configuration from database or settings"""
        # Get configuration from database or settings
        self.merchant_id = ZarinpalPaymentConfig.get_merchant_id()
        self.is_sandbox = ZarinpalPaymentConfig.get_is_sandbox()
        self.api_key = ZarinpalPaymentConfig.get_api_key()

        if self.is_sandbox:
            self.request_url = self.SANDBOX_API_REQUEST
            self.verify_url = self.SANDBOX_API_VERIFY
            self.payment_gateway = self.SANDBOX_PAYMENT_GATEWAY
            logger.info("Using Zarinpal sandbox mode")
        else:
            self.request_url = self.MAIN_API_REQUEST
            self.verify_url = self.MAIN_API_VERIFY
            self.payment_gateway = self.MAIN_PAYMENT_GATEWAY
            logger.info("Using Zarinpal production mode")

        logger.info(f"Zarinpal Merchant ID: {self.merchant_id}")
        logger.info(f"Request URL: {self.request_url}")

    def request_payment(
        self, amount: int, description: str, callback_url: str, mobile: Optional[str] = None, email: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Request a payment from Zarinpal

        Args:
            amount (int): Payment amount in Tomans
            description (str): Payment description
            callback_url (str): URL to redirect after payment
            mobile (str, optional): User's mobile number
            email (str, optional): User's email

        Returns:
            Tuple[bool, str, Dict[str, Any]]: (success, payment_url or error, response data)
        """
        data = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "description": description,
            "callback_url": callback_url,
        }

        if mobile:
            data["metadata"] = {"mobile": mobile}
            if email:
                data["metadata"]["email"] = email
        elif email:
            data["metadata"] = {"email": email}

        logger.info(f"Sending payment request to Zarinpal: {data}")

        try:
            # Add timeout and better error handling
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = requests.post(self.request_url, json=data, headers=headers, timeout=20)

            # Log the raw response for debugging
            logger.debug(f"Zarinpal response status: {response.status_code}")
            logger.debug(f"Zarinpal raw response: {response.text}")

            # Check if response is empty
            if not response.text:
                logger.error("Empty response from Zarinpal")
                return False, "Empty response from payment gateway", {"error": "empty_response"}

            try:
                result = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}, Response: {response.text}")
                return (
                    False,
                    "Invalid response from payment gateway",
                    {"error": "json_decode_error", "response": response.text},
                )

            # Updated response parsing for v4 API
            if response.status_code == 200 and result.get("data", {}).get("code") == 100:
                authority = result.get("data", {}).get("authority")
                if not authority:
                    logger.error(f"Authority not found in response: {result}")
                    return False, "Payment gateway error: Authority not found", result

                payment_url = self.payment_gateway.format(authority=authority)
                logger.info(f"Payment request successful. Authority: {authority}, URL: {payment_url}")
                return True, payment_url, {"Authority": authority}
            else:
                error_code = result.get("errors", {}).get("code", "unknown")
                error_message = self._get_error_message(error_code)
                logger.error(f"Zarinpal payment request failed: {error_code} - {error_message}")
                return False, error_message, result

        except requests.exceptions.Timeout:
            logger.error("Zarinpal request timed out")
            return False, "Connection timeout with payment gateway", {"error": "timeout"}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Zarinpal connection error: {str(e)}")
            return False, "Connection error with payment gateway", {"error": str(e)}
        except Exception as e:
            logger.error(f"Zarinpal unexpected error: {str(e)}")
            return False, "Unexpected error communicating with payment gateway", {"error": str(e)}

    def verify_payment(self, authority: str, amount: int) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Verify a payment with Zarinpal

        Args:
            authority (str): Payment authority from request_payment
            amount (int): Payment amount in Tomans

        Returns:
            Tuple[bool, Optional[str], Dict[str, Any]]: (success, ref_id or None, response data)
        """
        data = {
            "merchant_id": self.merchant_id,
            "authority": authority,
            "amount": amount,
        }

        logger.info(f"Verifying payment with Zarinpal: {data}")

        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = requests.post(self.verify_url, json=data, headers=headers, timeout=20)

            # Log the raw response for debugging
            logger.debug(f"Zarinpal verification response status: {response.status_code}")
            logger.debug(f"Zarinpal verification raw response: {response.text}")

            # Check if response is empty
            if not response.text:
                logger.error("Empty response from Zarinpal during verification")
                return False, None, {"error": "empty_response"}

            try:
                result = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error during verification: {e}, Response: {response.text}")
                return False, None, {"error": "json_decode_error", "response": response.text}

            # Updated response parsing for v4 API
            if response.status_code == 200 and result.get("data", {}).get("code") == 100:
                ref_id = result.get("data", {}).get("ref_id")
                if not ref_id:
                    logger.error(f"RefID not found in verification response: {result}")
                    return False, None, {"error": "ref_id_not_found"}

                logger.info(f"Payment verification successful. RefID: {ref_id}")
                return True, ref_id, result.get("data", {})
            else:
                error_code = result.get("errors", {}).get("code", "unknown")
                error_message = self._get_error_message(error_code)
                logger.error(f"Zarinpal verification failed: {error_code} - {error_message}")
                return False, None, result

        except requests.exceptions.Timeout:
            logger.error("Zarinpal verification request timed out")
            return False, None, {"error": "timeout"}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Zarinpal verification connection error: {str(e)}")
            return False, None, {"error": str(e)}
        except Exception as e:
            logger.error(f"Zarinpal verification unexpected error: {str(e)}")
            return False, None, {"error": str(e)}

    def _get_error_message(self, error_code: str) -> str:
        """Get error message for Zarinpal error code"""
        # Updated error codes for Zarinpal API v4
        error_messages = {
            "-1": "اطلاعات ارسال شده ناقص است",
            "-2": "IP یا مرچنت کد پذیرنده صحیح نیست",
            "-3": "با توجه به محدودیت‌های شاپرک امکان پرداخت با رقم درخواست شده میسر نمی‌باشد",
            "-4": "سطح تایید پذیرنده پایین‌تر از سطح نقره‌ای است",
            "-11": "درخواست مورد نظر یافت نشد",
            "-12": "امکان ویرایش درخواست میسر نمی‌باشد",
            "-21": "هیچ نوع عملیات مالی برای این تراکنش یافت نشد",
            "-22": "تراکنش ناموفق می‌باشد",
            "-33": "رقم تراکنش با رقم پرداخت شده مطابقت ندارد",
            "-34": "سقف تقسیم تراکنش از لحاظ تعداد یا رقم عبور نموده است",
            "-40": "اجازه دسترسی به متد مربوطه وجود ندارد",
            "-41": "اطلاعات ارسال شده مربوط به AdditionalData غیرمعتبر می‌باشد",
            "-42": "مدت زمان معتبر طول عمر شناسه پرداخت باید بین ۳۰ دقیقه تا ۴۵ روز باشد",
            "-54": "درخواست مورد نظر آرشیو شده است",
            "101": "عملیات پرداخت موفق بوده و قبلا PaymentVerification تراکنش انجام شده است",
        }

        return error_messages.get(str(error_code), f"خطای ناشناخته کد {error_code}")
