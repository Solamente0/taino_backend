import json
from abc import ABC, abstractmethod

import pycountry
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import transaction, IntegrityError
from django.db.models import Q
from model_bakery import baker

from apps.country.models import Country, City
from apps.document.models import TainoDocument
from apps.initializers.tasks import initialize_cities_task, initialize_country_flags_task, initialize_state_cities_task
from apps.initializers.tasks.state import initialize_states_task
from apps.initializers.tasks.state_city_chain import start_city_and_state_task_chain
from apps.setting.models import GeneralSetting
from apps.social_media.models import SocialMediaType
from base_utils.dictionary import json_extract
from base_utils.files import read_json
from base_utils.text import guess_text_direction

User = get_user_model()


class AbstractBaseInitializerStrategy(ABC):

    @abstractmethod
    def initialize(self, **kwargs):
        """"""


class UserInitializerStrategy(AbstractBaseInitializerStrategy):
    def initialize(self, **kwargs):
        try:
            super_admin, is_created = User.objects.get_or_create(
                email="super_admin@taino.ir",
                defaults={
                    "first_name": "مدیر",
                    "last_name": "کل ",
                    "pid": "super_admin",
                    "phone_number": "989307605866",
                    "is_active": True,
                    "is_staff": True,
                    "is_superuser": True,
                    "is_admin": True,
                },
            )
            if is_created:
                super_admin.set_password("super_admin")
                super_admin.save()

        except Exception as e:
            print(f"\nException in initializing super admin user ========>>> " + str(e), flush=True)


class FixtureInitializerStrategy(AbstractBaseInitializerStrategy):
    __fixtures = []

    def initialize(self, **kwargs):

        for fixture in self.__fixtures:
            try:
                call_command("loaddata", fixture)
            except Exception as e:
                print(f"\nException in initializing {fixture} fixture========>>> " + str(e), flush=True)


class CountryInitializerStrategy(AbstractBaseInitializerStrategy):

    def initialize(self, **kwargs):
        try:
            if not Country.objects.exists():

                country_data_path = settings.BASE_DIR.joinpath("apps/country/fixtures/country.json")
                with open(country_data_path, "r") as file:
                    json_data = json.load(file)

                for item in json_data:
                    fields = item["fields"]
                    flag_url = fields.pop("flag", None)
                    country = Country.objects.create(pk=item["pk"], **fields)

            if kwargs.get("download_country_flags", None):
                initialize_country_flags_task.apply_async()
        except Exception as e:
            print(f"\nException in initializing country fixture========>>> " + str(e), flush=True)


class StateInitializerStrategy(AbstractBaseInitializerStrategy):
    def initialize(self, **kwargs):
        if kwargs["state_modification"]:
            initialize_states_task.apply_async()


class StateCityInitializerStrategy(AbstractBaseInitializerStrategy):

    def initialize(self, **kwargs):
        if kwargs["state_modification"] and kwargs["city_modification"]:
            start_city_and_state_task_chain()
        elif kwargs["city_modification"]:
            initialize_state_cities_task.apply_async()
        elif kwargs["state_modification"]:
            initialize_states_task.apply_async()


class CityInitializerStrategy(AbstractBaseInitializerStrategy):

    def initialize(self, **kwargs):
        if not City.objects.exists():
            initialize_cities_task.apply_async()


class SocialMediaTypeInitializerStrategy(AbstractBaseInitializerStrategy):

    def initialize(self, **kwargs):
        try:
            data_path = settings.BASE_DIR.joinpath("apps/social_media/fixtures/social_media_type.json")
            with open(data_path, "r") as file:
                json_data = json.load(file)
            for item in json_data:
                social_type = item["fields"]["type"]
                if not SocialMediaType.objects.filter(type=social_type).exists():
                    SocialMediaType.objects.create(link=item["fields"]["link"], type=social_type)
        except Exception as e:
            print(f"\nException in initializing social media type ========>>> " + str(e), flush=True)


class GeneralSettingInitializerStrategy(AbstractBaseInitializerStrategy):

    def initialize(self, **kwargs):
        try:
            data_path = settings.BASE_DIR.joinpath("apps/setting/fixtures/settings.json")
            with open(data_path, "r") as file:
                json_data = json.load(file)
            for item in json_data:
                key = item.pop("key")
                if not GeneralSetting.objects.filter(key=key).exists():
                    GeneralSetting.objects.create(**item, key=key)
        except Exception as e:
            print(f"\nException in initializing settings ========>>> " + str(e), flush=True)


class DeepSeekAIInitializerStrategy(AbstractBaseInitializerStrategy):

    def initialize(self, **kwargs):
        try:
            from apps.chat.models import ChatAIConfig
            from django.contrib.auth import get_user_model

            admin = User.objects.filter(is_admin=True).first()
            data_path = settings.BASE_DIR.joinpath("apps/chat/fixtures/ai_config.json")
            with open(data_path, "r") as file:
                json_data = json.load(file)
            for item in json_data:
                static_name = item.pop("static_name")
                if not ChatAIConfig.objects.filter(static_name=static_name).exists():
                    ChatAIConfig.objects.create(**item, static_name=static_name, creator=admin)
        except Exception as e:
            print(f"\nException in initializing deepseek ai ========>>> " + str(e), flush=True)


class ServiceCategoryInitializerStrategy(AbstractBaseInitializerStrategy):
    """Initialize service categories"""

    def initialize(self, **kwargs):
        try:
            from apps.common.models import ServiceCategory

            data_path = settings.BASE_DIR.joinpath("apps/common/fixtures/service_category.json")
            if not data_path.exists():
                print(f"Service category fixture not found at {data_path}")
                return

            with open(data_path, "r", encoding="utf-8") as file:
                json_data = json.load(file)

            for item in json_data:
                fields = item["fields"]
                static_name = fields.get("static_name")

                if not ServiceCategory.objects.filter(static_name=static_name).exists():
                    ServiceCategory.objects.create(pk=item.get("pk"), **fields)
                    print(f"Created service category: {fields.get('name')}")
                else:
                    print(f"Service category already exists: {fields.get('name')}")

        except Exception as e:
            print(f"\nException in initializing service categories ========>>> {str(e)}", flush=True)


class ServiceItemInitializerStrategy(AbstractBaseInitializerStrategy):
    """Initialize service items"""

    def initialize(self, **kwargs):
        try:
            from apps.common.models import ServiceItem, ServiceCategory

            data_path = settings.BASE_DIR.joinpath("apps/common/fixtures/service_item.json")
            if not data_path.exists():
                print(f"Service item fixture not found at {data_path}")
                return

            with open(data_path, "r", encoding="utf-8") as file:
                json_data = json.load(file)

            for item in json_data:
                fields = item["fields"]
                static_name = fields.get("static_name")
                category_id = fields.pop("category")

                try:
                    category = ServiceCategory.objects.get(pk=category_id)
                except ServiceCategory.DoesNotExist:
                    print(f"Category with pk={category_id} not found, skipping {fields.get('name')}")
                    continue

                if not ServiceItem.objects.filter(static_name=static_name).exists():
                    ServiceItem.objects.create(pk=item.get("pk"), category=category, **fields)
                    print(f"Created service item: {fields.get('name')}")
                else:
                    print(f"Service item already exists: {fields.get('name')}")

        except Exception as e:
            print(f"\nException in initializing service items ========>>> {str(e)}", flush=True)


class GeneralChatAIConfigInitializerStrategy(AbstractBaseInitializerStrategy):
    """Initialize general chat AI configurations"""

    def initialize(self, **kwargs):
        try:
            from apps.ai_chat.models import GeneralChatAIConfig

            data_path = settings.BASE_DIR.joinpath("apps/ai_chat/fixtures/general_chat_ai_config.json")
            if not data_path.exists():
                print(f"General chat AI config fixture not found at {data_path}")
                return

            with open(data_path, "r", encoding="utf-8") as file:
                json_data = json.load(file)

            admin = User.objects.filter(is_admin=True).first()

            for item in json_data:
                fields = item["fields"]
                static_name = fields.get("static_name")

                if not GeneralChatAIConfig.objects.filter(static_name=static_name).exists():
                    GeneralChatAIConfig.objects.create(pk=item.get("pk"), creator=admin, **fields)
                    print(f"Created general chat AI config: {fields.get('name')}")
                else:
                    print(f"General chat AI config already exists: {fields.get('name')}")

        except Exception as e:
            print(f"\nException in initializing general chat AI configs ========>>> {str(e)}", flush=True)


class ChatAIConfigInitializerStrategy(AbstractBaseInitializerStrategy):
    """Initialize chat AI configurations"""

    def initialize(self, **kwargs):
        try:
            from apps.ai_chat.models import ChatAIConfig, GeneralChatAIConfig

            data_path = settings.BASE_DIR.joinpath("apps/ai_chat/fixtures/chat_ai_config.json")
            if not data_path.exists():
                print(f"Chat AI config fixture not found at {data_path}")
                return

            with open(data_path, "r", encoding="utf-8") as file:
                json_data = json.load(file)

            admin = User.objects.filter(is_admin=True).first()

            for item in json_data:
                fields = item["fields"]
                static_name = fields.get("static_name")
                general_config_id = fields.pop("general_config")

                try:
                    general_config = GeneralChatAIConfig.objects.get(pk=general_config_id)
                except GeneralChatAIConfig.DoesNotExist:
                    print(f"General config with pk={general_config_id} not found, skipping {fields.get('name')}")
                    continue

                if not ChatAIConfig.objects.filter(static_name=static_name).exists():
                    ChatAIConfig.objects.create(general_config=general_config, creator=admin, **fields)
                    print(f"Created chat AI config: {fields.get('name')}")
                else:
                    print(f"Chat AI config already exists: {fields.get('name')}")

        except Exception as e:
            print(f"\nException in initializing chat AI configs ========>>> {str(e)}", flush=True)
