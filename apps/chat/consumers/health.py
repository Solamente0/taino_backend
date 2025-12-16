import logging

from channels.generic.websocket import WebsocketConsumer

logger = logging.getLogger(__name__)


class DebugConsumer(WebsocketConsumer):
    def connect(self):
        print(f"🔍 DEBUG - Connection attempt to: {self.scope['path']}", flush=True)
        logger.debug(f"🔍 DEBUG - Connection attempt to: {self.scope['path']}")
        print(f"🔍 DEBUG - Headers: {dict(self.scope['headers'])}", flush=True)
        logger.debug(f"🔍 DEBUG - Headers: {dict(self.scope['headers'])}")
        print(f"🔍 DEBUG - Query string: {self.scope['query_string']}", flush=True)
        logger.debug(f"🔍 DEBUG - Query string: {self.scope['query_string']}")
        self.accept()
        self.send(text_data="Connected to debug consumer")

    def disconnect(self, close_code):
        print(f"🔍 DEBUG - Disconnected with code: {close_code}", flush=True)
        logger.debug(f"🔍 DEBUG - Disconnected with code: {close_code}")

    def receive(self, text_data=None, bytes_data=None):
        print(f"🔍 DEBUG - Received: {text_data}", flush=True)
        logger.debug(f"🔍 DEBUG - Received: {text_data}")

        self.send(text_data=f"Echo: {text_data}")


class HealthCheckConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.send(text_data="OK")
        self.close()
