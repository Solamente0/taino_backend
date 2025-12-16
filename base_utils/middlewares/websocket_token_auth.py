import logging
from urllib.parse import parse_qs

from channels.auth import AuthMiddleware, AuthMiddlewareStack, UserLazyObject
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from channels.sessions import CookieMiddleware, SessionMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from django.conf import settings
from django.db.models import Q
from jwt import decode as jwt_decode

# from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken

User = get_user_model()

"""[summary]
plucks the JWT access token from the query string and retrieves the associated user.
  Once the WebSocket connection is opened, all messages can be sent and received without
  verifying the user again. Closing the connection and opening it again
  requires re-authorization.
for example:
ws://localhost:8000/<route>/?token=<token_of_the_user>

"""

logger = logging.getLogger(__name__)


def get_token_from_header(header):
    pass


def get_token_from_query_string(q):
    pass


@database_sync_to_async
def get_user(scope):
    close_old_connections()
    headers = dict(scope["headers"])
    query_string = scope["query_string"].decode()
    query_token = parse_qs(query_string).get("token", None)
    print(f"qqqqqq::: {query_string}", flush=True)
    print(f"qqqqttt::: {query_token}", flush=True)

    token = None

    if b"authorization" in headers:
        auth_header = headers[b"authorization"].decode()
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
        elif len(parts) == 1 and parts[0].lower().startswith("ey"):
            token = parts[0]
    elif query_token is not None:
        token = query_token[0]  # ✅ Extract first item from list

    if not token:
        return AnonymousUser()

    try:
        # signing_key = settings.__getattr__("JWT_SIGNING_KEY") or settings.__getattr__("SECRET_KEY")
        # UntypedToken(token)
        # print(f"tttttt::: {token}", flush=True)
        # payload = jwt_decode(token, signing_key, algorithms=["HS256"])
        # user_id = payload.get("user_id") or payload.get("user_pid")
        # if not user_id:
        #     return AnonymousUser()
        #
        # user = User.objects.get(Q(id=user_id) | Q(pid=user_id))

        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(token)
        user = jwt_auth.get_user(validated_token)

        if not user.is_active:
            return AnonymousUser()
        return user
    except Exception as e:
        print(f"Token validation error: {e}", flush=True)
        return AnonymousUser()


class TokenAuthMiddleware(AuthMiddleware):
    async def resolve_scope(self, scope):
        scope["user"]._wrapped = await get_user(scope)
        print(f"hey scope! {scope=}", flush=True)

    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        logger.info(f"Processing WebSocket connection: {scope['path']}")
        logger.info(f"Processing WebSocket connection: {scope=}")
        # Scope injection/mutation per this middleware's needs.
        self.populate_scope(scope)
        # Grab the finalized/resolved scope
        await self.resolve_scope(scope)

        return await super().__call__(scope, receive, send)


def TokenAuthMiddlewareStack(inner):
    # print(f"infqeifnqeif: {inner.__dict__=}", flush=True)
    # print(f"infqeifnqeif: {inner.__dict__['routes']=}", flush=True)
    #
    # for route in inner.routes:
    #     if getattr(route, "path", None) == "/ws/health/":
    #         print(f'aparpatea: {getattr(route, "path", None)=}', flush=True)
    #         return inner
    print("hey socket!", flush=True)
    print(f"hey socket! {inner.__dict__=}", flush=True)
    return CookieMiddleware(SessionMiddleware(TokenAuthMiddleware(inner)))
    # return TokenAuthMiddleware(inner)
