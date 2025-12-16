import codecs
import json

from celery import shared_task
from django.conf import settings
from django.db.models import ProtectedError


@shared_task
def initialize_states_task():
    from apps.country.models import State, Country

    data_dir = settings.BASE_DIR.joinpath("apps/country/fixtures/cities")
    for active_country in settings.ACTIVE_COUNTRIES_TO_CREATE:
        data_path = data_dir.joinpath(f"{active_country}.json")
        with codecs.open(data_path, "r", "utf-8") as f:
            data = json.load(f)
        country = Country.objects.filter(code=active_country).first()
        if country:
            for state in State.objects.filter(country=country):
                try:
                    state.delete()
                except ProtectedError:
                    state.name = ""
                    state.save()
            for province in data["provinces"]:
                _ = province.pop("cities")
                state_name = province.pop("us_name")
                state = State.objects.filter(country=country, name="").first()
                if state:
                    state.name = state_name
                    state.save()
                else:
                    state = State.objects.create(country=country, name=state_name)
