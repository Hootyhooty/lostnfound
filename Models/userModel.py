from mongoengine import (
    Document, EmailField, StringField, BooleanField,
    DateTimeField, EnumField,IntField, ValidationError
)
from bcrypt import hashpw, gensalt, checkpw
import hashlib
import secrets
from datetime import datetime, timedelta
from enum import Enum
from hashids import Hashids
import os

# =====================================
#  HASHIDS CONFIGURATION
# =====================================
HASHIDS_SALT = os.getenv('HASHIDS_SALT', 'default-salt')
HASHIDS_MIN_LENGTH = int(os.getenv('HASHIDS_MIN_LENGTH', 16))
HASHIDS_ALPHABET = os.getenv(
    'HASHIDS_ALPHABET',
    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
)
hashids = Hashids(
    salt=HASHIDS_SALT,
    min_length=HASHIDS_MIN_LENGTH,
    alphabet=HASHIDS_ALPHABET
)


# =====================================
#  ROLE ENUM
# =====================================
class Role(Enum):
    USER = "user"
    ADMIN = "admin"


# =====================================
#  USER MODEL
# =====================================
class User(Document):
    name = StringField(required=True, unique=True, max_length=50)
    email = EmailField(required=True, unique=True)
    alternate_email = EmailField(required=False)
    first_name = StringField(max_length=50, required=False)
    last_name = StringField(max_length=50, required=False)
    photo = StringField(default="default.jpg")
    phone = IntField(required=True, unique=True)
    display_phone = BooleanField(default=False)
    role = EnumField(Role, default=Role.USER)
    password = StringField(required=True, min_length=8)
    password_confirm = StringField(required=False)
    password_changed_at = DateTimeField()
    password_reset_token = StringField()
    password_reset_expires = DateTimeField()
    active = BooleanField(default=True)
    # Address fields
    address_line1 = StringField(max_length=200, required=False)
    address_line2 = StringField(max_length=200, required=False)
    city = StringField(max_length=100, required=False)
    state = StringField(max_length=100, required=False)
    zipcode = StringField(max_length=20, required=False)
    country = StringField(max_length=100, required=False, default="United States")
    # Social media fields
    facebook = StringField(required=False)
    instagram = StringField(required=False)
    twitter = StringField(required=False)
    description = StringField(max_length=500, required=False)
    profile_slug = StringField(unique=True)
    # Reputation status
    email_verified = BooleanField(default=False)
    phone_verified = BooleanField(default=False)

    meta = {
        'collection': 'users',
        'indexes': ['email', 'password_reset_token', 'profile_slug']
    }

    # =====================================
    #  HELPERS
    # =====================================
    def generate_profile_slug(self):
        """Generate unique short slug based on ObjectId timestamp."""
        if not self.id:
            raise ValidationError("Cannot generate profile slug before ObjectId is assigned")

        unique_int = int(self.id.generation_time.timestamp() * 1000) + int(str(self.id)[18:], 16)
        slug = hashids.encode(unique_int)

        # Ensure no collision
        existing_user = User.objects(profile_slug=slug).first()
        if existing_user and str(existing_user.id) != str(self.id):
            raise ValidationError(f"HashID collision for slug {slug}")
        return slug

    def clean(self):
        """Validate and normalize user input before saving."""

        # ============================
        # Password confirmation check
        # ============================
        if self.password and self.password_confirm:
            if self.password != self.password_confirm:
                raise ValidationError("Passwords do not match!")
        self.password_confirm = None  # clear confirm before saving

        # ============================
        # Normalize email
        # ============================
        if self.email:
            self.email = self.email.strip().lower()

        # ============================
        # Normalize and validate phone
        # ============================
        if self.phone:
            # Accept either int or string, but store as int
            import re
            if isinstance(self.phone, str):
                cleaned = re.sub(r"\D", "", self.phone)  # remove non-digits
            else:
                cleaned = str(self.phone)

            if not cleaned.isdigit():
                raise ValidationError("Phone number must contain digits only.")
            if len(cleaned) < 8 or len(cleaned) > 15:
                raise ValidationError("Phone number length invalid (must be 8–15 digits).")

            self.phone = int(cleaned)

            # Check for duplicates (other users with same phone)
            existing_user = User.objects(phone=self.phone, id__ne=self.id).first()
            if existing_user:
                raise ValidationError("Phone number already in use.")

    # =====================================
    #  SAVE OVERRIDE
    # =====================================
    def save(self, *args, **kwargs):
        """Custom save method to handle password hashing and slug creation."""
        # Step 1: Validate input fields
        self.clean()

        # Step 2: Hash password if not already hashed
        if self.password and not self.password.startswith("$2b$"):
            self.password = hashpw(self.password.encode('utf-8'), gensalt(12)).decode('utf-8')
            self.password_changed_at = datetime.utcnow() - timedelta(seconds=1)

        # Step 3: Save once to get ObjectId
        if not self.id:
            super(User, self).save(*args, **kwargs)

        # Step 4: Generate slug (requires ObjectId)
        if not self.profile_slug:
            self.profile_slug = self.generate_profile_slug()

        # Optional debug output (remove later if needed)
        print(f"💾 Saving user to MongoDB: {self.email}")

        # Step 5: Final save
        return super(User, self).save(*args, **kwargs)

    # =====================================
    #  PASSWORD + SECURITY HELPERS
    # =====================================
    def correct_password(self, candidate_password: str) -> bool:
        """Check if provided password matches the stored hash."""
        return checkpw(candidate_password.encode('utf-8'), self.password.encode('utf-8'))

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return hashpw(password.encode('utf-8'), gensalt(12)).decode('utf-8')

    def create_password_reset_token(self) -> str:
        """Generate a secure password reset token."""
        reset_token = secrets.token_hex(32)
        self.password_reset_token = hashlib.sha256(reset_token.encode('utf-8')).hexdigest()
        self.password_reset_expires = datetime.utcnow() + timedelta(minutes=10)
        return reset_token

    # =====================================
    #  JSON SERIALIZER
    # =====================================
    def to_json(self) -> dict:
        """Convert user document to JSON-friendly dict."""
        return {
            'id': str(self.id),
            'name': self.name,
            'email': self.email,
            'alternate_email': getattr(self, 'alternate_email', None),
            'first_name': getattr(self, 'first_name', None),
            'last_name': getattr(self, 'last_name', None),
            'role': self.role.value if isinstance(self.role, Role) else self.role,
            'photo': self.photo,
            'phone': self.phone,
            'display_phone': getattr(self, 'display_phone', False),
            'address_line1': getattr(self, 'address_line1', None),
            'address_line2': getattr(self, 'address_line2', None),
            'city': getattr(self, 'city', None),
            'state': getattr(self, 'state', None),
            'zipcode': getattr(self, 'zipcode', None),
            'country': getattr(self, 'country', 'United States'),
            'facebook': getattr(self, 'facebook', None),
            'instagram': getattr(self, 'instagram', None),
            'twitter': getattr(self, 'twitter', None),
            'description': getattr(self, 'description', None),
            'active': self.active,
            'profile_slug': self.profile_slug,
            'email_verified': getattr(self, 'email_verified', False),
            'phone_verified': getattr(self, 'phone_verified', False)
        }
