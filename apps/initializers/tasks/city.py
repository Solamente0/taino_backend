import codecs
import json

from celery import shared_task
from django.conf import settings


@shared_task
def initialize_state_cities_task():
    from apps.country.models import Country, State, City

    data_dir = settings.BASE_DIR.joinpath("apps/country/fixtures/cities")
    for active_country in settings.ACTIVE_COUNTRIES_TO_CREATE:
        data_path = data_dir.joinpath(f"{active_country}.json")
        with codecs.open(data_path, "r", "utf-8") as f:
            data = json.load(f)
        country = Country.objects.filter(code=active_country).first()
        if country:
            # Delete or make empty the cities without any state
            for city in City.objects.filter(country=country, state__isnull=True):
                try:
                    city.delete()
                except Exception as e:
                    print(e, flush=True)
                    city.name = ""
                    city.save()

            for province in data["provinces"]:
                state = State.objects.filter(name=province["us_name"]).first()

                for city in City.objects.filter(country=country, state=state):
                    try:
                        city.delete()
                    except Exception as e:
                        print(e, flush=True)
                        city.name = ""
                        city.save()

                cs = province.pop("cities")

                for c in cs:
                    city_name = c.pop("us_name")

                    city = City.objects.filter(country=country, state=state, name="").first()
                    if city is None:
                        city = City.objects.filter(country=country, name="").first()

                    if city:
                        city.name = city_name
                        city.state = state
                        city.save()
                    else:
                        try:
                            city = City.objects.create(country=country, state=state, name=city_name)
                        except Exception as e:
                            print(e, flush=True)
