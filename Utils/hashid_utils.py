from hashids import Hashids
import os

# Centralized Hashids instance for generating short slugs
HASHIDS_SALT = os.getenv('HASHIDS_SALT', 'lostfound-default-salt')
HASHIDS_MIN_LENGTH = int(os.getenv('HASHIDS_MIN_LENGTH', 10))
HASHIDS_ALPHABET = os.getenv(
    'HASHIDS_ALPHABET',
    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
)

hashids = Hashids(salt=HASHIDS_SALT, min_length=HASHIDS_MIN_LENGTH, alphabet=HASHIDS_ALPHABET)

def encode_object_id(obj_id: str) -> str:
    """Encode a Mongo ObjectId (hex string) into a short slug using Hashids."""
    try:
        # Convert 24-char hex to int
        num = int(str(obj_id), 16)
        return hashids.encode(num)
    except Exception:
        return str(obj_id)

def decode_slug(slug: str) -> str | None:
    """Decode a slug back into an ObjectId hex string."""
    try:
        decoded = hashids.decode(slug)
        if not decoded:
            return None
        num = decoded[0]
        # Convert back to 24-char hex (pad with leading zeros)
        hex_id = format(num, 'x').zfill(24)
        return hex_id
    except Exception:
        return None


