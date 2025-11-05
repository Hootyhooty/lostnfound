import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import os

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "default_secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_IN_MINUTES = int(os.getenv("JWT_EXPIRES_IN_MINUTES", 60))
JWT_REFRESH_EXPIRES_IN_DAYS = int(os.getenv("JWT_REFRESH_EXPIRES_IN_DAYS", 7))

def create_access_token(user_id, role, expires_in_minutes=60):
    """
    Generate a JWT access token for a user.
    """
    payload = {
        "user_id": str(user_id),
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=expires_in_minutes),
        "iat": datetime.utcnow()
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token

def create_refresh_token(data: dict):
    """Generate a JWT refresh token."""
    payload = {
        **data,
        "exp": datetime.utcnow() + timedelta(days=JWT_REFRESH_EXPIRES_IN_DAYS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token):
    """
    Verify and decode a JWT token.
    Returns payload dict if valid, or None if invalid/expired.
    """
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
