from mongoengine import Document, ReferenceField, ListField, StringField, FloatField, IntField, DateTimeField
from datetime import datetime

class BasketItem(Document):
    product_code = StringField(required=True)  # e.g., 'mug', 'shirt', 'cap'
    name = StringField(required=True)
    qty = IntField(required=True)
    price = FloatField(required=True)  # price/unit
    # No _id for embedded
    meta = {'collection': 'none', 'strict': False}

class Sale(Document):
    user = ReferenceField('User', required=False)
    items = ListField(StringField())  # Will store dicts as JSON for flexibility
    total_price = FloatField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)
    status = StringField(default='created')  # 'created', 'paid', 'failed', ...
    payment_method = StringField()  # e.g. 'paypal', 'stripe'
    paypal_id = StringField()
    stripe_id = StringField()
    # Auditing identifiers
    paypal_capture_id = StringField()
    stripe_charge_id = StringField()
    stripe_receipt_url = StringField()
    item_count = IntField()

    meta = {
        'collection': 'sales',
        'indexes': ['user', 'created_at', 'status', 'payment_method']
    }
