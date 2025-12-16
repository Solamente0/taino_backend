from abc import ABC, abstractmethod
from datetime import datetime

from django.core.cache import cache


class AbstractCacheManager(ABC):
    @abstractmethod
    def get(self, key: str, **kwargs):
        pass

    @abstractmethod
    def set(self, key: str, value: str, **kwargs):
        pass

    @abstractmethod
    def delete(self, key: str, **kwargs):
        pass


class RedisCacheManager(AbstractCacheManager):
    def __init__(self):
        self.cache = cache
        super(RedisCacheManager, self).__init__()

    def get(self, key: str, **kwargs):
        return self.cache.get(key, **kwargs)

    def set(self, key: str, value: str, **kwargs):
        return self.cache.set(key, value, **kwargs)

    def delete(self, key: str, **kwargs):
        return self.cache.delete(key, **kwargs)

    def expire(self, key, at: datetime):
        return self.cache.expire_at(key, at)

    def ttl(self, key):
        return self.cache.ttl(key)

    def validity(self, key, value):
        return bool(self.cache.get(key) == value)
