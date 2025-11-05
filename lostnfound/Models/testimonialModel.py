from mongoengine import Document, StringField, ReferenceField, DateTimeField, BooleanField
from datetime import datetime


class Testimonial(Document):
    user = ReferenceField('User', required=True)
    message = StringField(required=True, max_length=1000)
    is_public = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'testimonial',
        'indexes': ['-created_at', 'user']
    }


