import logging
from typing import Optional, Union

import phonenumbers

log = logging.getLogger(__name__)


class DataSanitizer:

    @staticmethod
    def clean_phone_number(phone_number: str, country_alpha2: Optional[str] = None) -> Union[str, None]:
        """
        Removes leading 0 and country code
        """

        if not phone_number:
            return None

        try:

            phone_number = phone_number.strip().replace(" ", "")

            cleaned_phone = phonenumbers.parse(phone_number, country_alpha2).national_number
            if cleaned_phone:
                return str(cleaned_phone)
        except Exception as e:
            log.error(e)

        return None
