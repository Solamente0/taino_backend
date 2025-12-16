from abc import ABC
from typing import List

from django.conf import settings
from openai import OpenAI
from pydantic import BaseModel


class ItemSchema(BaseModel):
    msg: str
    translation: str


class TranslatedDataSchema(BaseModel):
    messages: List[ItemSchema]

    def to_list(self):
        return [
            {
                "msg": msg.msg,
                "translation": msg.translation,
            }
            for msg in self.messages
        ]


class AbstractTranslatorManager(ABC):
    api_key: str
    available_models: list
    default_model: str
    temperature = 0  # Less creative, more accurate
    max_tokens = 1000  # Token limit

    def connect(self):
        pass

    def translate(self, to_language_code: str, msgs: list):
        pass

    def parse_translations(self, output):
        pass


class ChatGPTTranslatorManager(AbstractTranslatorManager):
    """
    gpt model to support structured output
    https://platform.openai.com/docs/guides/structured-outputs/introduction
    """

    api_key: str
    available_models = ["gpt-4o-2024-08-06", "gpt-4o-mini-2024-07-18"]
    default_model = "gpt-4o-mini-2024-07-18"
    system_prompt = "You are a chat translation assistant. Translate messages using an informal, casual tone suitable for everyday ctainoersations. the output should be in list"

    def __init__(self, gpt_model=None, *args, **kwargs):
        self.api_key = settings.OPENAI_API_KEY
        self.gpt_model = gpt_model if gpt_model in self.available_models else self.default_model

        if gpt_model and gpt_model not in self.available_models:
            raise ValueError(f"{gpt_model} is not a valid model. Available models: {self.available_models}")

    def connect(self):
        return OpenAI(api_key=self.api_key)

    def translate(self, to_language_code: str, msgs: list, from_language_code: str = None):
        """
        Translate messages to the target language. Optionally, specify a source language.

        :param to_language_code: Target language code
        :param msgs: List of messages to translate
        :param from_language_code: Optional source language code
        :return: List of translated messages
        """
        # Create the prompt for GPT to translate in bulk
        client = self.connect()
        prompt = self.build_translation_prompt(msgs, to_language_code, from_language_code)
        completion = client.beta.chat.completions.parse(
            model=self.gpt_model,
            response_format=TranslatedDataSchema,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[
                {
                    "role": "system",
                    "content": self.system_prompt,
                },
                {"role": "user", "content": prompt},
            ],
        )

        translated_text = completion.choices[0].message.parsed

        # Parse the result into the expected format
        return self.parse_translations(translated_text)

    def build_translation_prompt(self, msgs, to_language_code, from_language_code=None):
        if from_language_code or from_language_code != "auto":
            prompt = f"Translate from language code: {from_language_code}, to language code: {to_language_code}:{msgs}"
        else:
            prompt = f"Translate to language code: {to_language_code}: {msgs}"
        return prompt

    def parse_translations(self, gpt_output) -> list:
        # Parse the GPT response into a list of dictionaries with actual msgs and translations
        if isinstance(gpt_output, TranslatedDataSchema):
            return gpt_output.to_list()

        raise ValueError(
            f"Expected GPT output to be a list, but got {type(gpt_output).__name__} instead. "
            "Ensure the response format is correct."
        )
