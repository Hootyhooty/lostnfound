import logging
from flask import request, jsonify
from datetime import datetime
from Models.lostItemModel import LostItem, ItemStatus, ItemCategory, VenueType
from Models.userModel import User
from Models.claimedItemModel import ClaimedItem
from Utils.appError import AppError
from Utils.auth_decorator import token_required
import json
from urllib import request as urlrequest

# ----------------------------------------
# Location validation via Zippopotam.us API
# ----------------------------------------
COUNTRY_NAME_TO_CODE = {
    "united states": "US",
    "usa": "US",
    "us": "US",
    "canada": "CA",
    "united kingdom": "GB",
    "uk": "GB",
    "australia": "AU",
    "germany": "DE",
    "france": "FR"
}

def validate_location(country: str, state: str, city: str, zipcode: str):
    """Validate location using Zippopotam.us when supported.

    Only validates for known countries in COUNTRY_NAME_TO_CODE. Returns
    (True, None) if valid or unsupported, otherwise (False, message).
    """
    if not country or not zipcode:
        return True, None

    code = COUNTRY_NAME_TO_CODE.get(str(country).strip().lower())
    if not code:
        # Unsupported country – skip validation gracefully
        return True, None

    try:
        url = f"http://api.zippopotam.us/{code}/{zipcode}"
        with urlrequest.urlopen(url, timeout=6) as resp:
            if resp.status != 200:
                return False, "Zip code not found for selected country."
            payload = json.loads(resp.read().decode("utf-8"))
            places = payload.get("places", [])
            if not places:
                return False, "Zip code has no places for selected country."

            # Basic city/state check (case-insensitive contains)
            desired_city = (city or "").strip().lower()
            desired_state = (state or "").strip().lower()
            for p in places:
                place_name = (p.get("place name") or "").strip().lower()
                state_name = (p.get("state") or "").strip().lower()
                if (not desired_city or desired_city in place_name) and (not desired_state or desired_state in state_name):
                    return True, None
            return False, "City/State do not match the zip code for the selected country."
    except Exception:
        # Network or API issue – do not block submission
        return True, None

logger = logging.getLogger(__name__)

@token_required
def create_lost_item(user):
    """Create a new lost item report."""
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        required_fields = ['title', 'category', 'specific_description', 'country', 'state_province', 'city_town', 'zipcode']
        for field in required_fields:
            if not data.get(field):
                raise AppError(f"{field.replace('_', ' ').title()} is required", 400)
        
        # Parse date_lost if provided, otherwise use current date
        date_lost = datetime.utcnow()
        if data.get('date_lost'):
            try:
                date_lost = datetime.fromisoformat(data['date_lost'].replace('Z', '+00:00'))
            except ValueError:
                raise AppError("Invalid date format for date_lost", 400)
        
        # Validate location (non-blocking for unsupported countries or API errors)
        ok, msg = validate_location(
            country=data.get('country'),
            state=data.get('state_province'),
            city=data.get('city_town'),
            zipcode=str(data.get('zipcode')) if data.get('zipcode') is not None else None
        )
        if not ok:
            raise AppError(msg or "Invalid location details", 400)

        # Validate and set status
        status = data.get('status', ItemStatus.LOST.value)
        if status not in [e.value for e in ItemStatus]:
            status = ItemStatus.LOST.value
        
        # Parse latitude and longitude to float if provided
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        latitude = float(latitude) if latitude not in (None, '', 'null') else None
        longitude = float(longitude) if longitude not in (None, '', 'null') else None

        # Create the lost item
        lost_item = LostItem(
            title=data['title'],
            status=status,
            date_lost=date_lost,
            category=data['category'],
            sub_category=data.get('sub_category'),
            brand_breed=data.get('brand_breed'),
            model=data.get('model'),
            serial_id_baggage_claim=data.get('serial_id_baggage_claim'),
            primary_color=data.get('primary_color'),
            secondary_color=data.get('secondary_color'),
            specific_description=data['specific_description'],
            specific_location=data.get('specific_location'),
            address=data.get('address'),
            country=data['country'],
            state_province=data['state_province'],
            city_town=data['city_town'],
            zipcode=data['zipcode'],
            venue_type=data.get('venue_type', VenueType.NA.value),
            images=data.get('images', []),
            reported_by=user,
            latitude=latitude,
            longitude=longitude
        )
        
        lost_item.save()
        
        logger.info(f"✅ Lost item created by {user.email}: {lost_item.id}")
        
        return jsonify({
            "success": True,
            "message": "Lost item reported successfully",
            "data": lost_item.to_json()
        }), 201
        
    except AppError as e:
        raise e
    except Exception as e:
        logger.error(f"Error creating lost item: {str(e)}")
        raise AppError(f"Error creating lost item: {str(e)}", 500)

@token_required
def get_user_lost_items(user):
    """Get all lost items reported by the current user."""
    try:
        items = LostItem.objects(reported_by=user, is_active=True).order_by('-created_at')
        
        return jsonify({
            "success": True,
            "data": [item.to_json() for item in items]
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching user lost items: {str(e)}")
        raise AppError(f"Error fetching lost items: {str(e)}", 500)

@token_required
def get_lost_item_by_id(user, item_id):
    """Get a specific lost item by ID."""
    try:
        item = LostItem.objects(id=item_id, reported_by=user).first()
        if not item:
            raise AppError("Lost item not found", 404)
        
        return jsonify({
            "success": True,
            "data": item.to_json()
        }), 200
        
    except AppError as e:
        raise e
    except Exception as e:
        logger.error(f"Error fetching lost item {item_id}: {str(e)}")
        raise AppError(f"Error fetching lost item: {str(e)}", 500)

@token_required
def update_lost_item(user, item_id):
    """Update a lost item report."""
    try:
        item = LostItem.objects(id=item_id, reported_by=user).first()
        if not item:
            raise AppError("Lost item not found", 404)
        
        data = request.get_json() or {}
        
        # Update allowed fields
        updatable_fields = [
            'title', 'sub_category', 'brand_breed', 'model', 'serial_id_baggage_claim',
            'primary_color', 'secondary_color', 'specific_description',
            'specific_location', 'address', 'country', 'state_province',
            'city_town', 'zipcode', 'venue_type', 'images', 'latitude', 'longitude'
        ]
        
        for field in updatable_fields:
            if field in data:
                if field in ['latitude', 'longitude']:
                    value = data[field]
                    if value in (None, '', 'null'):
                        setattr(item, field, None)
                    else:
                        setattr(item, field, float(value))
                else:
                    setattr(item, field, data[field])
        
        # Handle date_lost separately
        if 'date_lost' in data and data['date_lost']:
            try:
                item.date_lost = datetime.fromisoformat(data['date_lost'].replace('Z', '+00:00'))
            except ValueError:
                raise AppError("Invalid date format for date_lost", 400)
        
        item.save()
        
        logger.info(f"✅ Lost item updated by {user.email}: {item.id}")
        
        return jsonify({
            "success": True,
            "message": "Lost item updated successfully",
            "data": item.to_json()
        }), 200
        
    except AppError as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating lost item {item_id}: {str(e)}")
        raise AppError(f"Error updating lost item: {str(e)}", 500)

@token_required
def delete_lost_item(user, item_id):
    """Soft delete a lost item report."""
    try:
        item = LostItem.objects(id=item_id, reported_by=user).first()
        if not item:
            raise AppError("Lost item not found", 404)
        
        item.is_active = False
        item.save()
        
        logger.info(f"✅ Lost item deleted by {user.email}: {item.id}")
        
        return jsonify({
            "success": True,
            "message": "Lost item deleted successfully"
        }), 200
        
    except AppError as e:
        raise e
    except Exception as e:
        logger.error(f"Error deleting lost item {item_id}: {str(e)}")
        raise AppError(f"Error deleting lost item: {str(e)}", 500)

@token_required
def claim_lost_item(user, item_id):
    """Move an item to claimed_items and delete original."""
    try:
        item = LostItem.objects(id=item_id, reported_by=user).first()
        if not item:
            raise AppError("Lost item not found", 404)

        data = item.to_mongo().to_dict()
        data.pop('_id', None)
        claimed = ClaimedItem(**data)
        claimed.status = 'claimed'
        claimed.updated_at = datetime.utcnow()
        claimed.save()

        item.delete()

        logger.info(f"✅ Item {item_id} moved to claimed_items")
        return jsonify({"success": True, "message": "Item marked as claimed"}), 200
    except AppError as e:
        raise e
    except Exception as e:
        logger.error(f"Error claiming lost item {item_id}: {str(e)}")
        raise AppError(f"Error claiming lost item: {str(e)}", 500)
