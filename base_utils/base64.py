import base64
import uuid

import six
from django.core.files.base import ContentFile
from rest_framework import serializers

from base_utils.files import get_file_format, get_file_extension_by_base64_uri


class Base64FileField(serializers.FileField):
    """
    A Django REST framework field for handling file uploads through raw post data.
    It uses base64 for encoding and decoding the contents of the file.
    """

    def to_internal_value(self, data):
        # Check if this is a base64 string
        if isinstance(data, six.string_types):
            # Check if the base64 string is in the "data:" format
            b64 = data
            if "data:" in data and ";base64," in data:
                # Break out the header from the base64 content
                header, data = data.split(";base64,")
            else:
                self.fail("invalid")
            # Try to decode the file. Return validation error if it fails.
            try:
                if data.startswith("http") or data.startswith("api"):
                    return None
                decoded_file = base64.b64decode(data)
            except TypeError:
                decoded_file = ""
                self.fail("invalid")
            if decoded_file == "":
                return None
            # Generate file name:
            file_name = str(uuid.uuid4())[:12]  # 12 characters are more than enough.
            # Get the file name extension:
            file_extension = get_file_format(file_name, decoded_file)
            if file_extension is None:
                file_extension = get_file_extension_by_base64_uri(b64)
            complete_file_name = "%s.%s" % (
                file_name,
                file_extension,
            )
            data = ContentFile(decoded_file, name=complete_file_name)
        return super(Base64FileField, self).to_internal_value(data)
