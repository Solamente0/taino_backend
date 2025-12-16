import json

from django.conf import settings
from django.db.models import Count

from apps.country.models import City, Country, State


def ctainoert_cities_to_cities_en():

    all_cities = City.objects.all()

    for city in all_cities.iterator():
        try:
            city.delete()
        except Exception as e:
            print("Exception in removing Cities", flush=True)

    print("Finished Deleting", flush=True)

    # cities that are in a relationship :D will be set null to be filled by further data first
    all_cities = City.objects.all()
    for city in all_cities.iterator():
        try:
            city.name = None
            city.save()
        except Exception as e:
            print("Exception in making city name null", flush=True)

    print("Finished Nulling", flush=True)
    # reading json file of en cities

    city_data_path = settings.BASE_DIR.joinpath("apps/country/fixtures/cities_en.json")
    with open(city_data_path, "r") as file:
        data = json.load(file)

    for data_item in data:
        country_code = data_item.get("country_iso2", None)
        print(country_code, flush=True)
        if country_code:
            country = Country.objects.filter(code=country_code).first()

            if country:

                city_names = data_item.get("cities_en", [])

                for city_name in city_names:
                    try:
                        city_name = city_name.strip()
                    except Exception as e:
                        print("Error in striping city name string", flush=True)
                    city_with_null_name = City.objects.filter(country=country, name__isnull=True).first()

                    if city_with_null_name:
                        city_with_null_name.name = city_name
                        city_with_null_name.save()

                    else:
                        City.objects.create(country=country, name=city_name)

    print("Finished Importing Data", flush=True)


def remove_duplicate_cities():
    """
    Gathered data has some duplicates, this script removes duplicate cities that are in same country and state
    """

    duplicates = (
        City.objects.values("name", "country", "state").annotate(name_count=Count("name")).filter(name_count__gt=1)
    )  #

    print(len(duplicates))

    for dup in duplicates:
        name = dup["name"]
        country = dup["country"]
        state = dup["state"]
        print(name, country, state, sep=" , ", flush=True)

        instances = City.objects.filter(
            name=name,
            country=country,
            state=state,
        )
        # Keep the first instance and delete the rest
        if instances.exists():
            instances.exclude(id=instances.first().id).delete()
