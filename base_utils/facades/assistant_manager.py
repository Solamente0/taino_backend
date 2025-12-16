from abc import ABC

import openai
from django.conf import settings
from openai import OpenAI


class AbstractAssistantManager(ABC):
    api_key: str
    available_models: list
    default_model: str
    temperature = 0.6  # higher value will be more creative and less accurate
    max_tokens = 500  # Token limit
    chat_history = []
    prompt = None

    def add_message(self, role: str, content: str):
        pass

    def chat(self, user_message: str):
        pass

    def reset_chat_history(self):
        self.chat_history = []

    def get_chat_history(self):
        return self.chat_history

    def set_chat_history(self, chat_history: list):
        self.chat_history = chat_history

    def set_prompt(self, prompt):
        self.prompt = prompt


class ChatGptAssistantManager(AbstractAssistantManager):

    def __init__(self, model=None, temperature=0.6, max_tokens=500):
        self.api_key = settings.OPENAI_API_KEY
        openai.api_key = self.api_key
        self.model = model or settings.ASSISTANT_DEFAULT_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.chat_history = []

    def add_message(self, role: str, content: str):
        self.chat_history.append({"role": role, "content": [
            {"type": "text", "text": content}
        ]})

    def connect(self):
        return OpenAI(api_key=self.api_key)

    def chat(self, user_message: str):
        """
        Handle a new user message, get a response from ChatGPT, and update chat history.
        """
        self.add_message("user", user_message)

        client = self.connect()
        completion = client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=self.chat_history,
        )

        assistant_message = completion.choices[0].message.content

        self.add_message("assistant", assistant_message)

        return assistant_message


# if __name__ == '__main__':
#     import sys, os
#     sys.path.append(
#         '/home/solamente/Documents/porjects/taino-backend'
#     )
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
#     import django
#
#     django.setup()
#     x = ChatGptAssistantManager().chat("Hi")
#     print(x)