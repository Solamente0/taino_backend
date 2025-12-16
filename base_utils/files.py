import json
import os

import imghdr

from django.utils import timezone
from django.utils.deconstruct import deconstructible


@deconstructible
class FileRenamePathGenerator(object):
    def __init__(self, sub_path, part):
        self.path = sub_path
        self.part = part
        self.final_path = None

    def __call__(self, instance, filename):
        ext = filename.split(".")[-1]
        filename = "{}.{}".format(self.part + "-" + timezone.now().strftime("%m/%d/%Y-%H:%M:%S"), ext)
        self.final_path = os.path.join(self.path, filename)
        return self.final_path


@deconstructible
class FilePathGenerator(object):
    def __init__(self, sub_path, part):
        self.path = sub_path
        self.part = part
        self.final_path = None

    def __call__(self, instance, filename):
        ext = filename.split(".")[-1]
        final_name = "{}.{}".format(
            self.part + "-" + timezone.now().strftime("%m/%d/%Y-%H%M%S") + "/" + filename,
            ext,
        )
        self.final_path = os.path.join(self.path, final_name)
        return self.final_path


def get_file_extension(file) -> str | None:
    name, extension = os.path.splitext(file.name)
    if extension == "pdf":
        return "pdf"
    elif extension == "docx":
        return "docx"
    elif extension == "doc":
        return "doc"
    elif extension == "jpg":
        return "jpg"
    elif extension == "jpeg":
        return "jpeg"
    elif extension == "png":
        return "png"
    return None


def read_json(file_path, mode="r"):
    try:
        with open(file_path, mode) as file:
            json_data = json.load(file)
        return json_data
    except Exception as e:
        raise e


def get_file_format(file_name, decoded_file):
    """Try to get the file extension based on the decoded file content"""
    extension = imghdr.what(None, decoded_file)
    if extension:
        return extension

    # For non-image files, try to guess from the file name
    if "." in file_name:
        return file_name.split(".")[-1]

    return "bin"  # Default binary extension


def get_file_extension_by_base64_uri(base64_uri):
    """Get file extension from base64 string if available"""
    if "data:" in base64_uri and ";base64," in base64_uri:
        header = base64_uri.split(";base64,")[0]
        # Handle common mime types
        if header.startswith("data:image/"):
            return header.replace("data:image/", "").replace(";", "")
        if header.startswith("data:application/"):
            return header.replace("data:application/", "").replace(";", "")
        if header.startswith("data:video/"):
            return header.replace("data:video/", "").replace(";", "")
        if header.startswith("data:audio/"):
            return header.replace("data:audio/", "").replace(";", "")
    return None
