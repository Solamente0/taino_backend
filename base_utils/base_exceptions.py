from rest_framework.exceptions import APIException


class TainoException(Exception):
    pass


class TainoAPIException(APIException):
    pass


class ServiceUnavailable(TainoAPIException):
    status_code = 503
    default_detail = "Service temporarily unavailable, try again later."
    default_code = "service_unavailable"

class MethodNotAvailableForAdmin(TainoAPIException):
    status_code = 503
    default_detail = "This method is not available for admin."
    default_code = "service_unavailable"
