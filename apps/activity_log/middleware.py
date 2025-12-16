"""
apps/activity_log/middleware.py
Optional middleware for automatic activity logging
"""

import logging
from django.utils.deprecation import MiddlewareMixin

from apps.activity_log.models import ActivityLogAction, ActivityLogLevel
from apps.activity_log.services.logger import ActivityLogService

logger = logging.getLogger(__name__)


class ActivityLogMiddleware(MiddlewareMixin):
    """
    Middleware for automatically logging certain activities.
    Add to MIDDLEWARE in settings.py to enable.

    Note: This logs ALL requests, which can generate many logs.
    Consider using selective logging in views instead.
    """

    # Paths to exclude from automatic logging
    EXCLUDED_PATHS = [
        "/admin/",
        "/static/",
        "/media/",
        "/api/ping",
        "/api/schema/",
    ]

    # Methods to log automatically
    LOGGED_METHODS = ["POST", "PUT", "PATCH", "DELETE"]

    def process_response(self, request, response):
        """Log the request after processing"""

        # Skip excluded paths
        if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return response

        # Only log certain methods
        if request.method not in self.LOGGED_METHODS:
            return response

        # Only log if user is authenticated
        if request.user is None:
            return response
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return response

        try:
            # Determine action based on method
            action_map = {
                "POST": ActivityLogAction.CREATE,
                "PUT": ActivityLogAction.UPDATE,
                "PATCH": ActivityLogAction.UPDATE,
                "DELETE": ActivityLogAction.DELETE,
            }

            action = action_map.get(request.method, ActivityLogAction.OTHER)

            # Determine success based on status code
            is_successful = 200 <= response.status_code < 400
            level = ActivityLogLevel.INFO if is_successful else ActivityLogLevel.ERROR

            # Log the activity
            ActivityLogService.log(
                user=request.user,
                action=action,
                description=f"{request.method} {request.path}",
                request=request,
                level=level,
                is_successful=is_successful,
                metadata={
                    "status_code": response.status_code,
                },
            )

        except Exception as e:
            logger.error(f"Error in ActivityLogMiddleware: {e}")

        return response
