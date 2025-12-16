import uuid
import logging

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.authentication.models import UserDevice
from config.renderer import CustomJSONRenderer

logger = logging.getLogger(__name__)


class SingleDeviceMiddleware(MiddlewareMixin):
    """
    Middleware to ensure a user can only be logged in from one device at a time.
    It checks for an active session and compares device information.
    """

    def get_client_ip(self, request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def get_device_id(self, request):
        """Get or create device ID from cookies or headers"""
        # First check if there's a device_id in the cookie
        device_id = request.COOKIES.get("device_id")

        # If not, check if there's one in the headers
        if not device_id:
            device_id = request.META.get("HTTP_X_DEVICE_ID")

        # If still no device_id, generate one
        if not device_id:
            device_id = str(uuid.uuid4())

        return device_id

    def process_request(self, request):
        """Process each request to check device authorization"""
        # Skip this middleware for admin paths and non-authenticated requests
        response_data = {
            "result": {},
            "status": 403,
            "success": False,
            "error_messages": {},
        }
        print(f"refqqqqpatt === {request.path=}", flush=True)
        if (
            request.path.startswith("/admin/")
            or request.path.startswith("/api/auth/v1/login/")
            or request.path.startswith("/api/auth/v1/logout/")
        ):
            return None

        # Try to authenticate with JWT
        jwt_auth = JWTAuthentication()
        try:
            jwt_response = jwt_auth.authenticate(request)
            if jwt_response:
                user, _ = jwt_response
                # User is authenticated, check device
                if user and user.is_authenticated:
                    device_id = self.get_device_id(request)
                    ip_address = self.get_client_ip(request)
                    user_agent = request.META.get("HTTP_USER_AGENT", "")

                    # Get active device for this user
                    active_device = UserDevice.get_active_device(user)
                    print(f"here84 {active_device=}")
                    print(f"here84 {device_id=}")
                    # If there's an active device and it's not this one
                    if active_device and active_device.device_id != device_id:
                        # Existing active session on another device
                        error_message = (
                            "شما هم اکنون در یک دستگاه دیگر وارد شده اید! برای ورود باید ابتدا از آن دستگاه خارج شوید!"
                        )
                        response_data["error_messages"]["non_field_errors"] = error_message
                        print(f"resppp ==== {response_data=}", flush=True)
                        return JsonResponse(response_data, status=status.HTTP_403_FORBIDDEN)
                    # If no active device or this is the active device
                    # if not active_device:
                    # Create new device record
                    # UserDevice.objects.create(
                    #     user=user, device_id=device_id, user_agent=user_agent, ip_address=ip_address, is_active=True
                    # )
                    # elif active_device.device_id == device_id:
                    if active_device.device_id == device_id:
                        # Update last login time
                        active_device.ip_address = ip_address
                        active_device.user_agent = user_agent
                        active_device.save(update_fields=["ip_address", "user_agent", "last_login"])

        except PermissionDenied:
            error_message = "شما هم اکنون در یک دستگاه دیگر وارد شده اید! برای ورود باید ابتدا از آن دستگاه خارج شوید!"
            # raise PermissionDenied(
            #     "شما هم اکنون در یک دستگاه دیگر وارد شده اید! برای ورود باید ابتدا از آن دستگاه خارج شوید!"
            # )
            response_data["error_messages"]["non_field_errors"] = error_message

            return JsonResponse(response_data, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            logger.exception(f"Error in SingleDeviceMiddleware: {e}")
        return None

    def process_response(self, request, response):
        """Process response to set device_id cookie if needed"""
        if not request.COOKIES.get("device_id"):
            device_id = self.get_device_id(request)
            # Set the cookie for 1 year
            response.set_cookie("device_id", device_id, max_age=31536000, httponly=True, samesite="Lax")
        return response
