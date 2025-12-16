# services.py
import logging
import urllib
from typing import Dict, Any

from django.core.exceptions import ValidationError

import config.settings.constants
from apps.authentication.models import TainoUser
from base_utils.facades.http import HttpRequestManager

log = logging.getLogger(__name__)

google_auth_request = HttpRequestManager()


class GoogleAuth:
    def __init__(self, code):
        self.code = code

    def get_access_token(self, code: str) -> str:
        data = {
            "code": code,
            "client_id": config.settings.constants.GOOGLE_AUTH_CONFIG["GOOGLE_OAUTH2_CLIENT_ID"],
            "client_secret": config.settings.constants.GOOGLE_AUTH_CONFIG["GOOGLE_OAUTH2_CLIENT_SECRET"],
            "redirect_uri": config.settings.constants.GOOGLE_AUTH_CONFIG["GOOGLE_OAUTH2_REDIRECT_URI"],
            "grant_type": "authorization_code",
        }
        params = urllib.parse.urlencode(data)

        response = google_auth_request.post(
            config.settings.constants.GOOGLE_AUTH_CONFIG["GOOGLE_ACCESS_TOKEN_OBTAIN_URL"] + "?" + params
        )
        if not response.ok:
            log.error("Response.json() for get access_token")
            log.error(response.json())
            print(response.json(), flush=True)
            raise ValidationError("Could not get access token from Google.")

        access_token = response.json()["access_token"]

        return access_token

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        response = google_auth_request.get(
            config.settings.constants.GOOGLE_AUTH_CONFIG["GOOGLE_USER_INFO_URL"], params={"access_token": access_token}
        )

        if not response.ok:
            log.error(f"google auth response data: {response.data}")
            print(response.json(), flush=True)
            raise Exception("google service is unavailable")

        return response.json()

    def login(self):
        access_token = self.get_access_token(code=self.code)
        user_data = self.get_user_info(access_token)
        # Creates user in DB if first time login
        query = TainoUser.objects.filter(email=user_data["email"])
        if not query.exists():
            TainoUser.objects.create(
                email=user_data["email"],
                first_name=user_data.get("given_name"),
                last_name=user_data.get("family_name"),
            )

        profile_data = {
            "email": user_data["email"],
            "first_name": user_data.get("given_name"),
            "last_name": user_data.get("family_name"),
        }
        return profile_data
