import sys

from .base import env

TESTING = sys.argv[1:2] == ["test"]

DEFAULT_OTP_EXPIRE_TIME = env.int("DEFAULT_OTP_EXPIRE_TIME", default=120)
DEFAULT_OTP_LENGTH = env.int("DEFAULT_OTP_LENGTH", default=6)
VERIFICATION_TEMPLATE_ID = env.int("VERIFICATION_TEMPLATE_ID", default=602388)
COUNTRY_INITIALIZATION_MAX_API_CALL_COUNT = env.int("COUNTRY_INITIALIZATION_MAX_API_CALL_COUNT", default=5)

ACTIVE_COUNTRIES_TO_CREATE = ["IR"]

DEFAULT_AVATAR_PID = env("DEFAULT_AVATAR_PID", default="01j67hzyvysfvns17yjwtnbeqf")


# Zarinpal settings
ZARINPAL_MERCHANT_ID = env.str("ZARINPAL_MERCHANT_ID", default="YOUR-ZARINPAL-MERCHANT-ID")
ZARINPAL_SANDBOX = env.bool("ZARINPAL_SANDBOX", default=True)  # Set to False in production

# Base URL for callbacks
BASE_URL = env.str("BASE_URL", default="http://localhost:8000")
FRONTEND_URL = env.str("FRONTEND_URL", default="http://localhost:5173")
LOGIN_REDIRECT_URL = "/"

# Chat Constants
CHAT_MONGO_ENABLED = env.bool("CHAT_MONGO_ENABLED", default=False)
CHAT_MONGO_URI = "mongodb://localhost:27017/"  # Update with your MongoDB URI
CHAT_MONGO_DB = "vekalat_chat"

TAINO_SECRETARY_RECEIPIENT_EMAIL = env.str("TAINO_SECRETARY_RECEIPIENT_EMAIL", default="ataino@gmail.com")

PAYMENT_SUCCESS_FRONT_BASE_URL = env.str(
    "PAYMENT_SUCCESS_FRONT_BASE_URL", default="https://app.taino.ir/dashboard/wallet/success"
)
PAYMENT_FAILURE_FRONT_BASE_URL = env.str(
    "PAYMENT_FAILURE_FRONT_BASE_URL", default="https://app.taino.ir/dashboard/wallet/failed"
)
PAYMENT_CANCELED_FRONT_BASE_URL = env.str(
    "PAYMENT_CANCELED_FRONT_BASE_URL", default="https://app.taino.ir/dashboard/wallet/canceled"
)
