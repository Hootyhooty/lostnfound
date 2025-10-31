from mongoengine import Document, StringField, ReferenceField, DateTimeField, ListField, BooleanField
from datetime import datetime

class Message(Document):
    sender = ReferenceField('User', required=True)
    receiver = ReferenceField('User', required=True)
    item = ReferenceField('LostItem', required=True)
    title = StringField(required=True, max_length=200)
    body = StringField(required=True, max_length=3000)
    images = ListField(StringField())
    read = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'messages',
        'indexes': ['receiver', 'sender', 'created_at']
    }

