from .constants import TESTING
from .third_party import REST_FRAMEWORK

if not TESTING:

    REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ]
    REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
        "anon": "50/minute",
        "user": "500/minute",
        "auth": "7/minute",
        "map_mobile": "10/hour",  # todo should be incremental throttling
        "map_admin": "10/minute",
    }
