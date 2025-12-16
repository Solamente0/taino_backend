import logging

import requests
from requests import Response

log = logging.getLogger(__name__)


class HttpRequestManager:
    def __init__(self, headers: dict = None):
        self.headers = headers

    def post(self, url: str, data: dict, **kwargs) -> Response:
        try:
            return requests.post(url, headers=self.headers, json=data, **kwargs)
        except Exception as e:
            log.info(f"exception {e} occurred! while sending POST REQUEST!")
            pass

    def delete(self, url: str, **kwargs) -> Response:
        try:
            return requests.delete(url, headers=self.headers, **kwargs)
        except Exception as e:
            log.info(f"exception {e} occurred! while sending DELETE REQUEST!")

    def get(self, url, **kwargs) -> Response:
        try:
            return requests.get(url, headers=self.headers, **kwargs)
        except Exception as e:
            log.info(f"exception {e} occurred! while sending GET REQUEST!")
