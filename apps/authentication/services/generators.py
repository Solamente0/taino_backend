import base64

from django.conf import settings


class GenerateKey:
    @staticmethod
    def get_b74_key(key):
        value = str(key) + getattr(settings, "SECRET_KEY", None)
        return base64.b32encode(value.encode())
