import json
import os
import random
import time

from celery import shared_task
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files import File

from apps.country.models import Country
from apps.document.models import TainoDocument
from base_utils.facades.http import HttpRequestManager
from base_utils.randoms import generate_unique_public_id


@shared_task
def initialize_country_flags_task(api_call_delay: int = None) -> None:
    if not api_call_delay:
        api_call_delay = random.randint(5, 10)

    country_data_path = settings.BASE_DIR.joinpath("apps/country/fixtures/country.json")
    with open(country_data_path, "r") as file:
        json_data = json.load(file)

    for item in json_data:

        try:
            fields = item["fields"]
            flag_url = fields.get("flag", None)
            country_code = fields.get("code", None)

            country = Country.objects.filter(code=country_code).first()

            if country and country.flag is None:
                time.sleep(api_call_delay)
                country_content_type = ContentType.objects.get_for_model(Country)
                response = HttpRequestManager().get(flag_url)

                if response and response.status_code == 200:
                    document = TainoDocument(
                        pid=generate_unique_public_id(),
                        content_type=country_content_type,
                        object_id=country.id,
                        is_public=True,
                    )

                    file_path = f"/tmp/flag{random.randint(10000, 1000000)}.svg"
                    with open(file_path, "wb") as f:
                        f.write(response.content)

                    with open(file_path, "rb") as f:
                        document.file.save(os.path.basename(file_path), File(f), save=True)
                        document.save()
                        country.flag = document
                        country.save()
        except Exception as e:
            print(f"Error in Initializing a Country Flag. =====> {str(e)}")


@shared_task
def initialize_cities_task():
    from apps.country.models import City, Country

    city_data_path = settings.BASE_DIR.joinpath("apps/country/fixtures/cities_en.json")
    with open(city_data_path, "r") as file:
        data = json.load(file)

    for data_item in data:
        country_code = data_item.get("country_iso2", None)
        if country_code:
            country = Country.objects.filter(code=country_code).first()

            if country:

                city_names = data_item.get("cities_en", [])

                for city_name in city_names:
                    try:
                        city_name = city_name.strip()
                    except Exception as e:
                        print("Error in striping city name string", flush=True)

                    else:
                        try:
                            City.objects.create(country=country, name=city_name)
                        except Exception as e:
                            print("Error in creating city", e, flush=True)

    from apps.initializers.covert_scripts import remove_duplicate_cities

    remove_duplicate_cities()
