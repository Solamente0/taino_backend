from abc import ABC, abstractmethod

from config.settings import third_party as settings


class AbstractNoSQLManager(ABC):
    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def connect(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_db(self, *args, **kwargs):
        pass

    @abstractmethod
    def set(self, *args, **kwargs):
        pass

    @abstractmethod
    def update(self, *args, **kwargs):
        pass

    @abstractmethod
    def delete(self, *args, **kwargs):
        pass


class MongoManager(AbstractNoSQLManager):
    def __init__(self, db_name: str, *args, **kwargs):
        self.db_name: str = db_name
        self.connect = self.connect()
        self.db = self.get_db()

    def connect(self, *args, **kwargs):
        connection = settings.mongoengine
        return connection

    def get_db(self, *args, **kwargs):
        return self.connect.get_db()

    def get_collection(self, collection_name: str, **kwargs):
        return self.db.get_collection(collection_name)

    def create_collection(self, collection_name: str, *args, **kwargs):
        return self.db.create_collection(collection_name)

    def get_collection_names(self, filters=None, **kwargs):
        return self.db.list_collection_names()

    def get_collection_list(self, filters=None, **kwargs):
        return self.db.list_collections()

    def set(self, doc, *args, **kwargs):
        obj = doc(**kwargs)
        obj.save()
        return obj

    def update(self, doc, filters, *args, **kwargs):
        obj = doc(**filters).update(**kwargs)
        obj.reload()
        return obj

    def delete(self, doc, filters, *args, **kwargs):
        obj = self.update(doc, filters, *args, **kwargs)
        obj.reload()
        return obj

    def fetch_one(self, *args, **kwargs):
        pass

    def fetch_many(self, *args, **kwargs):
        pass
