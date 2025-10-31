from mongoengine import connect
from dotenv import load_dotenv
import os
from urllib.parse import urlparse

load_dotenv()

def init_db():
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/lostnfound_db")

    # Auto-detect DB name from URI
    parsed = urlparse(mongo_uri)
    db_name = (parsed.path or "").lstrip("/") or "lostnfound_db"

    try:
        connect(
            db=db_name,
            host=mongo_uri,
            alias="default"
        )
        print(f"✅ MongoDB connected successfully → {db_name}")
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        raise
