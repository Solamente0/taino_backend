"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

# import os
#
# from django.core.asgi import get_asgi_application
#
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
#
# application = get_asgi_application()
from .wsgi import *
from .settings import env

import os
import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()  # This is the critical line that's missing
from base_utils.middlewares import TokenAuthMiddlewareStack
from django.urls import path, re_path

from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from apps.chat.consumers.health import HealthCheckConsumer, DebugConsumer

# from channels.auth import AuthMiddlewareStack

from apps.chat import routing as chat_routing
from apps.ai_chat import routing as ai_chat_routing
from apps.ai_support import routing as ai_support_routing

import logging

logger = logging.getLogger(__name__)


application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        # "websocket": AllowedHostsOriginValidator(
        "websocket": TokenAuthMiddlewareStack(
            URLRouter(
                chat_routing.websocket_urlpatterns
                + ai_chat_routing.websocket_urlpatterns
                + ai_support_routing.websocket_urlpatterns
            )
        ),
    }
)
logger.info("ASGI application loaded with WebSocket support and debug middleware")
