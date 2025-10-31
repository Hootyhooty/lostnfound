from mongoengine import Document, StringField, FileField, DateTimeField
from datetime import datetime

class AllImgs(Document):
    filename = StringField(required=True, unique=True)
    file = FileField(required=True)  # Stored in GridFS
    content_type = StringField(default="image/jpeg")
    uploaded_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'all_imgs'}
