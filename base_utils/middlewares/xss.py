import json
from copy import deepcopy

from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseBadRequest


class XSSProtectionMiddleware(MiddlewareMixin):

    def process_request(self, request):
        temp = request.body  # do not remote this line

        if request.method in ("POST", "PATCH", "PUT"):
            try:
                if request.method == "POST":
                    data = json.dumps(request.POST)
                elif request.body:
                    data = json.loads(request.body.decode())

                from bleach import clean

                result = deepcopy(data)
                original_dump = json.dumps(result)

                # https://github.com/mozilla/bleach/issues/192
                cleaned = clean(original_dump, strip=True, tags=[], attributes=[]).replace("&amp;", "&")
                if cleaned != original_dump:  # is XSS
                    return HttpResponseBadRequest(status=400, content=b"Malformed Input", content_type="application/json")
            except:
                pass

            return None
