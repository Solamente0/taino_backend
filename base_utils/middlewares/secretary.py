import logging
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger(__name__)


class SecretaryMiddleware(MiddlewareMixin):
    """
    Middleware to handle secretary access to lawyer functionality

    This middleware checks if the current user is a secretary and if so,
    adds information about their lawyer to the request, allowing them
    to access the lawyer's resources.
    """

    def process_request(self, request):
        logger.info("SecretaryMiddleware processing request")

        user = getattr(request, "user", None)
        logger.info(f"User: {user}")

        # Check if user is a secretary
        is_secretary = False
        acting_as_lawyer = None

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            jwt_auth = JWTAuthentication()
            try:
                auth_header = request.META.get("HTTP_AUTHORIZATION", "")
                if auth_header.startswith("Bearer "):
                    raw_token = auth_header.split(" ")[1]
                    validated_token = jwt_auth.get_validated_token(raw_token)
                    user = jwt_auth.get_user(validated_token)
                    # Optional: Set the user on the request
                    request.user = user
                    logger.info(f"JWT authentication successful for user: {user}")

                    # Check if the user has a profile
                    logger.info(f"User has profile: {hasattr(user, 'profile')}")

                else:
                    logger.info("No Bearer token found in Authorization header")
            except Exception as e:
                logger.info(f"JWT authentication failed: {e}")

        try:
            if hasattr(user, "profile") and user.profile.lawyer:
                # Store the lawyer in the request
                is_secretary = True
                acting_as_lawyer = user.profile.lawyer

                # For logging/tracking purposes
                logger.info(f"Secretary {user.pid} acting on behalf of lawyer {user.profile.lawyer.pid}")
        except Exception as e:
            logger.error(f"Error in SecretaryMiddleware: {e}")

        # Set the attributes on the request
        request.is_secretary_request = is_secretary
        request.acting_as_lawyer = acting_as_lawyer

        logger.info(f"Set request.is_secretary_request = {request.is_secretary_request}")
        logger.info(f"Set request.acting_as_lawyer = {request.acting_as_lawyer}")

        return None
        # # Check if user is a secretary
        # if hasattr(user, "role") and user.role and user.role.static_name == "secretary":
        #     # Get the lawyer associated with this secretary
        #     try:
        #         if hasattr(user, "profile") and user.profile.lawyer:
        #             # Store the lawyer in the request
        #             request.acting_as_lawyer = user.profile.lawyer
        #             # Add a flag to indicate this request is being made by a secretary
        #             request.is_secretary_request = True
        #             # For logging/tracking purposes
        #             logger.info(f"Secretary {user.pid} acting on behalf of lawyer {user.profile.lawyer.pid}")
        #     except Exception as e:
        #         logger.error(f"Error in SecretaryMiddleware: {e}")
