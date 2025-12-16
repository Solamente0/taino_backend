import json

from django.http import JsonResponse
from django.test.client import RequestFactory
from rest_framework import status
from base_utils.base_tests import TainoBaseServiceTestCase
from base_utils.middlewares import XSSProtectionMiddleware


class XSSProtectionMiddlewareTests(TainoBaseServiceTestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.get_response = lambda request: JsonResponse({"message": "response"})  # Dummy response callable
        self.middleware = XSSProtectionMiddleware(self.get_response)

    def process_request_through_middleware(self, request):
        response = self.middleware.process_request(request)
        return response

    def test_valid_post_request(self):
        request = self.factory.post("/notes/", {"title": "new idea"}, format="json")
        response = self.process_request_through_middleware(request)
        self.assertIsNone(response)  # No response means request passed through middleware

    def test_invalid_post_request_with_xss(self):
        request = self.factory.post("/notes/", {"title": "<script>alert(1)</script>"}, format="json")
        response = self.process_request_through_middleware(request)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content, b"Malformed Input")

    def test_valid_patch_request(self):
        data = json.dumps({"title": "updated idea"})
        request = self.factory.patch("/notes/1/", data, content_type="application/json")
        response = self.process_request_through_middleware(request)
        self.assertIsNone(response)  # No response means request passed through middleware

    def test_invalid_patch_request_with_xss(self):
        data = json.dumps({"title": "<script>alert(1)</script>"})
        request = self.factory.patch("/notes/1/", data, content_type="application/json")
        response = self.process_request_through_middleware(request)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content, b"Malformed Input")

    def test_valid_put_request(self):
        data = json.dumps({"title": "another updated idea"})
        request = self.factory.put("/notes/1/", data, content_type="application/json")
        response = self.process_request_through_middleware(request)
        self.assertIsNone(response)  # No response means request passed through middleware

    def test_invalid_put_request_with_xss(self):
        data = json.dumps({"title": "<script>alert(1)</script>"})
        request = self.factory.put("/notes/1/", data, content_type="application/json")
        response = self.process_request_through_middleware(request)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content, b"Malformed Input")
