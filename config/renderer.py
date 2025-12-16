from rest_framework.renderers import JSONRenderer
from rest_framework.status import is_success


class CustomJSONRenderer(JSONRenderer):

    DEFAULT_ERROR_KEY = "non_field_errors"
    DRF_DEFAULT_ERROR_KEY_FOR_VALIDATION = "detail"

    def handle_error_list(self, errors, parent_key="") -> dict:
        return {parent_key or self.DEFAULT_ERROR_KEY: error for error in errors}

    def flatten_errors(self, errors, parent_key="") -> dict:
        flat_errors = {}
        if self.DRF_DEFAULT_ERROR_KEY_FOR_VALIDATION in errors.keys():
            value = errors.pop(self.DRF_DEFAULT_ERROR_KEY_FOR_VALIDATION)
            new_key = self.DEFAULT_ERROR_KEY
            errors[new_key] = value

        if self.is_error_of_drf_list_field(errors):
            errors = self.flat_drf_list_field_errors(errors)

        for key, value in errors.items():
            new_key = f"{key}" if parent_key else key

            if isinstance(value, list):
                if value and isinstance(value[0], dict):
                    for item in value:
                        flat_errors.update(self.flatten_errors(item, new_key))
                else:
                    flat_errors.update(self.handle_error_list(value, new_key))
            elif isinstance(value, dict):
                flat_errors.update(self.flatten_errors(value, new_key))
            else:
                flat_errors[new_key] = value
        return flat_errors

    def render(self, data, accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {}
        response = renderer_context["response"]
        status_code = response.status_code
        success = is_success(status_code)

        if success:
            try:
                response_data = {
                    "result": data,
                    "status": status_code,
                    "success": success,
                    "error_messages": {},
                }
            except Exception:
                response_data = {
                    "result": data,
                    "status": status_code,
                    "success": success,
                    "error_messages": {},
                }
        else:
            if isinstance(data, dict):
                errors = self.flatten_errors(data)
            elif isinstance(data, list):
                errors = self.handle_error_list(data)

            else:
                errors = {self.DEFAULT_ERROR_KEY: data}

            response_data = {
                "result": [],
                "status": status_code,
                "success": success,
                "error_messages": errors,
            }

        return super(CustomJSONRenderer, self).render(response_data, accepted_media_type, renderer_context)

    def is_error_of_drf_list_field(self, errors):
        """
        errors sample:
        {'files': {0: [ErrorDetail(string='Upload a valid image. The file you uploaded was either not an image or a corrupted image.', code='invalid_image')]}}
        """

        if isinstance(errors, dict):
            if len(errors.keys()) == 1:
                keys = list(errors.keys())
                value = errors[keys[0]]
                if isinstance(value, dict):
                    value_keys = list(value.keys())
                    if value_keys:
                        if isinstance(value_keys[0], int):
                            return True

        return False

    def flat_drf_list_field_errors(self, errors):
        """
        errors sample:
        {'files': {0: [ErrorDetail(string='Upload a valid image. The file you uploaded was either not an image or a corrupted image.', code='invalid_image')]}}
        """
        keys = list(errors.keys())
        value = errors[keys[0]]
        value_keys = list(value.keys())
        inner_value = value[value_keys[0]]
        if isinstance(inner_value, list) and inner_value:
            inner_value = inner_value[0]

        return {keys[0]: inner_value}
