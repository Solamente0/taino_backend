from mongoengine import Document, StringField

from base_utils.randoms import generate_unique_public_id


class BaseDocument(Document):

    # mark: variables

    pid = StringField(required=True, primary_key=True)

    # mark: meta

    meta = {
        "abstract": True,
        "allow_inheritance": True,
        "indexes": ["id"],
    }

    def save(self, **kwargs):
        if self.pid is None:
            self.pid = generate_unique_public_id()
        return super(BaseDocument, self).save(**kwargs)

    def update(self, **kwargs):
        return super(BaseDocument, self).update(**kwargs)
