import logging

logger = logging.getLogger(__name__)


def get_client_ip(request):
    try:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
    except Exception as e:
        logger.info(e)
        return ""


def get_user_data(request):
    try:
        user = request.user
        if user:
            return f"PID={user.pid} PHONE={user.phone_number} EMAIL={user.email}"
    except Exception as e:
        logger.info(e)

    return None


class RequestDetailMiddlewareLog:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        api_route = request.META.get("PATH_INFO")
        request_body = request.body
        user_agent = request.META.get("HTTP_USER_AGENT")
        params = request.META.get("QUERY_STRING")

        response = self.get_response(request)

        logger.info(f"User: {get_user_data(request)}")
        logger.info(f"API Route: {api_route}")
        logger.info(f"User Agent: {user_agent}")
        logger.info(f"User IP: {get_client_ip(request)}")
        logger.info(f"API Params: {params}")

        if not ("api/auth/" in api_route or "api/user/" in api_route):
            if len(request_body) < 100:
                logger.info(f"Request Body: {request_body}")

        return response
