import pycountry
from django.core.exceptions import ObjectDoesNotExist


def get_country_alpha2_from_currency(currency_code):
    """Find country Alpha-2 codes for a given currency code."""
    countries_with_currency = []

    # Iterate through all countries in pycountry
    for country in pycountry.countries:
        try:
            # Get the country's official currency
            country_currency = pycountry.currencies.get(numeric=country.numeric)
            if country_currency and country_currency.alpha_3 == currency_code:
                countries_with_currency.append(country.alpha_2)
        except AttributeError:
            # Some countries may not have numeric or currency info
            continue

    return countries_with_currency


def get_country_from_alpha2(data=None):
    counter = 0
    try:
        for key, value in data.items():
            country_code = value["2_alpha_country_code"]
            country = pycountry.countries.get(alpha_2=country_code)
            if country:
                print(f"Details for {key}:")
                print(f"  Country Name: {country.name}")
                print(f"  Alpha-2 Code: {country.alpha_2}")
                print(f"  Alpha-3 Code: {country.alpha_3}")
                print(f"  Numeric Code: {country.numeric}")
            else:
                counter += 1
                print(f"No details found for country code: {country_code}")

    except Exception as e:
        print(f"Exception: {e} in get_country_from_alpha2!")

    print(f"Missed Countries {counter=}")


def import_flags(json_data):
    for k, v in json_data.items():
        url = f"https://safetest.ir/taino/icons/flags/1x1/{v['2_alpha_country_code'].lower()}.svg"
        try:
            from apps.finance.models import Asset
            from base_utils.taino_document import save_document_from_url

            asset = Asset.objects.get(symbol=v["3_alpha_symbol"])
            doc = save_document_from_url(url=url, content_object=asset)
            asset.icon = doc
            asset.save()
            print(f"Successfully updated {asset.name} with icon.")
        except ObjectDoesNotExist:
            print(f"Asset with symbol {v['3_alpha_symbol']} does not exist.")
        except Exception as e:
            print(f"Error updating {v['name']}: {e}")
