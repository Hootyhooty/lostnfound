from mongoengine import Document, StringField, BooleanField, DateTimeField, IntField, ListField, ReferenceField
from datetime import datetime

class ClaimedItem(Document):
    # Mirror LostItem fields minimally
    title = StringField(max_length=200)
    status = StringField()
    date_lost = DateTimeField()
    category = StringField()
    sub_category = StringField()
    brand_breed = StringField()
    model = StringField()
    serial_id_baggage_claim = StringField()
    primary_color = StringField()
    secondary_color = StringField()
    specific_description = StringField()
    specific_location = StringField()
    address = StringField()
    country = StringField()
    state_province = StringField()
    city_town = StringField()
    zipcode = StringField()
    venue_type = StringField()
    images = ListField(StringField())
    reported_by = ReferenceField('User')
    created_at = DateTimeField()
    updated_at = DateTimeField(default=datetime.utcnow)
    is_active = BooleanField(default=True)

    meta = { 'collection': 'claimed_items' }

