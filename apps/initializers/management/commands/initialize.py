from django.core.management.base import BaseCommand

from ..command_strategy import (
    # StateCityInitializerStrategy,
    UserInitializerStrategy,
    FixtureInitializerStrategy,
    CountryInitializerStrategy,
    # CityInitializerStrategy,
    SocialMediaTypeInitializerStrategy,
    GeneralSettingInitializerStrategy,
    DeepSeekAIInitializerStrategy,
    ServiceCategoryInitializerStrategy,
    ServiceItemInitializerStrategy,
    GeneralChatAIConfigInitializerStrategy,
    ChatAIConfigInitializerStrategy,
)


class Command(BaseCommand):
    __initializers = [
        UserInitializerStrategy,
        FixtureInitializerStrategy,
        CountryInitializerStrategy,
        # CityInitializerStrategy,
        # StateCityInitializerStrategy,
        SocialMediaTypeInitializerStrategy,
        GeneralSettingInitializerStrategy,
        DeepSeekAIInitializerStrategy,
        ServiceCategoryInitializerStrategy,
        ServiceItemInitializerStrategy,
        GeneralChatAIConfigInitializerStrategy,
        ChatAIConfigInitializerStrategy,
    ]

    def add_arguments(self, parser):
        parser.add_argument("--state_modification", action="store_true", help="set this to modify the states")
        parser.add_argument("--city_modification", action="store_true", help="set this to modify the cities")
        parser.add_argument("--download_country_flags", action="store_true", help="set this to initialize country flags")

    def handle(self, *args, **options):
        for strategy in self.__initializers:
            try:
                strategy().initialize(**options)
            except Exception as e:
                print(e)
