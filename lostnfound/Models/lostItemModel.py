from mongoengine import (
    Document, StringField, BooleanField, DateTimeField, 
    IntField, ListField, ReferenceField, ValidationError, FloatField
)
from datetime import datetime
from enum import Enum

class ItemStatus(Enum):
    LOST = "lost"
    FOUND = "found"
    RETURNED = "returned"
    CLOSED = "closed"

class VenueType(Enum):
    NA = "N/A"
    AIRPORT = "Airport"
    AMUSEMENT_THEME_PARK = "Amusement / Theme park"
    ANIMAL_CONTROL_SHELTER = "Animal control / Shelter"
    ANIMAL_HOSPITAL_VET_CLINIC = "Animal hospital / Vet clinic"
    APARTMENT_CONDO_DORM_HOUSING = "Apartment / Condo / Dorm / Housing"
    ARENA_CIVIC_CENTER_STADIUM = "Arena / Civic center / Stadium"
    BAR_RESTAURANT_CLUB_CAFE = "Bar / Restaurant / Club / Cafe"
    BEACH_LAKE = "Beach / Lake"
    BUS_BUS_STATION = "Bus / Bus station"
    CAR_RENTAL = "Car rental"
    CONCERTS_EVENTS = "Concerts / Events"
    COUNTRY_CLUB_GOLF_COURSE = "Country club / Golf course"
    GAS_STATION_CONVENIENCE_STORE = "Gas station / Convenience store"
    GROCERY_STORE_SUPERMARKET = "Grocery store / Supermarket"
    GYM_POOL_SPORTS_COMPLEX = "Gym / Pool / Sports complex"
    HISTORICAL_PLACE = "Historical place"
    HOSPITAL = "Hospital"
    HOME_RENTAL_PROPERTY = "Home / Rental property"
    HOTEL_MOTEL_CASINO_RESORT_AREA = "Hotel / Motel / Casino / Resort area"
    LAUNDRY_MAT_LAUNDROMAT_DRY_CLEANER = "Laundry mat / Laundromat / Dry cleaner"
    LIBRARY = "Library"
    LOCAL_PARK = "Local park"
    MUSEUM = "Museum"
    OFFICE_COMPLEX = "Office complex"
    PARKING_GARAGE = "Parking garage"
    PARK = "Park"
    POLICE = "Police"
    REST_AREA = "Rest area"
    SCHOOL = "School"
    SHIP = "Ship"
    SHIP_PORT = "Ship port"
    FERRY = "Ferry"
    FERRY_PORT = "Ferry port"
    SKI_AREA = "Ski area"
    STATE_NATIONAL_PARK = "State / National park"
    STORE_MALL = "Store / Mall"
    TAXI_LIMO = "Taxi / Limo"
    THEATER_CINEMA = "Theater / Cinema"
    TRAIN_TRAIN_STATION = "Train / Train station"
    TRANSIT_SYSTEM = "Transit system"
    WORSHIP_CENTER = "Worship center"
    ZOO_AQUARIUM = "Zoo / Aquarium"

class ItemCategory(Enum):
    ANIMALS_PET = "Animals / pet"
    BAGS_BAGGAGE_LUGGAGE = "Bags / Baggage / Luggage"
    CLOTHING = "Clothing"
    COLLECTORS_ITEMS = "Collectors items"
    CURRENCY_MONEY = "Currency / Money"
    DOCUMENTS_LITERATURE = "Documents / Literature"
    ELECTRONICS = "Electronics"
    HOUSEHOLD_TOOLS = "Household / Tools"
    JEWELRY = "Jewelry"
    MAIL_PARCEL = "Mail / Parcel"
    MEDIA = "Media"
    MEDICAL = "Medical"
    MUSIC_INSTRUMENTS = "Music instruments"
    PERSONAL_ACCESSORIES = "Personal accessories"
    SPORTING_GOODS = "Sporting goods"
    TICKETS = "Tickets"
    TOYS = "Toys"
    TRANSPORTATION = "Transportation"
    VISUAL_ART_RELATED = "Visual art related"

class LostItem(Document):
    # Basic Information
    title = StringField(max_length=200, required=True)  # Item title/name
    status = StringField(choices=[(e.value, e.value) for e in ItemStatus], default=ItemStatus.LOST.value, required=True)
    date_lost = DateTimeField(required=True, default=datetime.utcnow)
    category = StringField(choices=[(e.value, e.value) for e in ItemCategory], required=True)
    sub_category = StringField(max_length=100)  # Sub-category based on main category
    brand_breed = StringField(max_length=100)  # For animals
    model = StringField(max_length=100)
    serial_id_baggage_claim = StringField(max_length=100)
    primary_color = StringField(max_length=50)
    secondary_color = StringField(max_length=50)
    latitude = FloatField()  # Latitude for pinpoint
    longitude = FloatField()  # Longitude for pinpoint
    
    # Description and Location
    specific_description = StringField(required=True, max_length=1000)
    specific_location = StringField(max_length=500)
    
    # Location Information (Required)
    address = StringField(max_length=500)
    country = StringField(required=True, max_length=100)
    state_province = StringField(required=True, max_length=100)
    city_town = StringField(required=True, max_length=100)
    zipcode = StringField(required=True, max_length=20)
    
    # Venue Information
    venue_type = StringField(choices=[(e.value, e.value) for e in VenueType], default=VenueType.NA.value)
    
    # Images
    images = ListField(StringField())  # Store filenames of uploaded images
    
    # User Information
    reported_by = ReferenceField('User', required=True)
    
    # Timestamps
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    # Status tracking
    is_active = BooleanField(default=True)
    
    meta = {
        'collection': 'lost_items',
        'indexes': [
            'status',
            'category',
            'country',
            'state_province',
            'city_town',
            'reported_by',
            'created_at'
        ]
    }
    
    def clean(self):
        """Validate the lost item data before saving."""
        # Ensure date_lost is not in the future
        if self.date_lost and self.date_lost > datetime.utcnow():
            raise ValidationError("Date lost cannot be in the future")
    
    def save(self, *args, **kwargs):
        """Custom save method to handle validation and timestamps."""
        self.clean()
        self.updated_at = datetime.utcnow()
        return super(LostItem, self).save(*args, **kwargs)
    
    def to_json(self):
        """Convert lost item document to JSON-friendly dict."""
        return {
            'id': str(self.id),
            'title': self.title,
            'status': self.status,
            'date_lost': self.date_lost.isoformat() if self.date_lost else None,
            'category': self.category,
            'sub_category': self.sub_category,
            'brand_breed': self.brand_breed,
            'model': self.model,
            'serial_id_baggage_claim': self.serial_id_baggage_claim,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'specific_description': self.specific_description,
            'specific_location': self.specific_location,
            'address': self.address,
            'country': self.country,
            'state_province': self.state_province,
            'city_town': self.city_town,
            'zipcode': self.zipcode,
            'venue_type': self.venue_type,
            'images': self.images,
            'reported_by': str(self.reported_by.id) if self.reported_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'latitude': self.latitude,
            'longitude': self.longitude
        }
