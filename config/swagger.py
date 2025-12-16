from django.conf import settings
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import OpenApiParameter


class CustomAutoSchema(AutoSchema):
    global_params = [
        OpenApiParameter(
            name="accept-language",
            type=str,
            location=OpenApiParameter.HEADER,
            description=f"`fa` | `en` | `tr` | `fr` | `de` | `ru` | `ar` | `es`",
            enum=[l[0] for l in settings.LANGUAGES],
            default=settings.LANGUAGE_CODE,
        )
    ]

    def get_override_parameters(self):
        params = super().get_override_parameters()
        return params + self.global_params
