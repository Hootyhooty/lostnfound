from flask import request, jsonify, current_app
from functools import wraps
from Utils.appError import AppError
from Models.lostItemModel import LostItem
from Models.userModel import User
from Utils.jwt_utils import decode_token
from Utils.hashid_utils import encode_object_id
from mongoengine import Q
import math
from datetime import datetime
import re
import traceback

def require_auth(f):
    """Decorator to require authentication for search endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            raise AppError("Authentication required", 401)
        
        token = token.split(' ')[1]
        try:
            decoded = decode_token(token)
            if not decoded or 'user_id' not in decoded:
                raise AppError("Invalid token", 401)
            user_id = decoded['user_id']
            return f(user_id, *args, **kwargs)
        except Exception as e:
            raise AppError("Authentication failed", 401)
    return decorated_function

@require_auth
def search_items(user_id):
    """
    Search for lost/found items with various filters
    """
    try:
        data = request.get_json() or {}
        
        # Log the search request for debugging
        current_app.logger.info(f"Search request from user {user_id}: {data}")
        
        # Extract search parameters
        keyword = data.get('keyword', '').strip()
        status = data.get('status', '').strip()
        category = data.get('category', '').strip()
        sub_category = data.get('subCategory', '').strip()
        country = data.get('country', '').strip()
        state = data.get('state', '').strip()
        city = data.get('city', '').strip()
        zipcode = data.get('zipcode', '').strip()
        radius = data.get('radius')
        near_me = data.get('near_me', False)
        by_venue = data.get('by_venue', False)
        page = int(data.get('page', 1))
        per_page = 10
        
        # Build MongoDB query using Q objects
        query_conditions = []
        
        # Status filter
        if status:
            # Handle both lowercase and capitalized status values from database
            # Use case-insensitive search for status
            normalized_status = status.lower()
            query_conditions.append(Q(status__icontains=normalized_status))
        
        # Category filters
        if category:
            query_conditions.append(Q(category__icontains=category))
        
        if sub_category:
            query_conditions.append(Q(sub_category__icontains=sub_category))
        
        # Location filters
        if country:
            query_conditions.append(Q(country__icontains=country))
        
        if state:
            query_conditions.append(Q(state_province__icontains=state))
        
        if city:
            query_conditions.append(Q(city_town__icontains=city))
        
        if zipcode:
            if radius:
                # Simplified radius search - just search zipcode pattern
                query_conditions.append(Q(zipcode__icontains=zipcode))
            else:
                query_conditions.append(Q(zipcode__icontains=zipcode))
        
        # Near me search (requires user location)
        if near_me:
            user = User.objects(id=user_id).first()
            if user and hasattr(user, 'location') and user.location:
                # Use user's location for radius search
                # Simplified: just check nearby cities/states
                if hasattr(user.location, 'city'):
                    query_conditions.append(Q(city_town__icontains=user.location.city))
            else:
                raise AppError("User location not available for 'near me' search", 400)
        
        # Text search across multiple fields
        if keyword:
            if by_venue:
                # Venue-based search
                keyword_query = Q(title__icontains=keyword) | Q(specific_description__icontains=keyword) | Q(specific_location__icontains=keyword)
            else:
                # General keyword search across all fields
                keyword_query = (Q(title__icontains=keyword) | 
                                Q(specific_description__icontains=keyword) | 
                                Q(category__icontains=keyword) | 
                                Q(sub_category__icontains=keyword) | 
                                Q(specific_location__icontains=keyword))
            
            query_conditions.append(keyword_query)
        
        # If no filters provided, return all items
        if not any([keyword, status, category, sub_category, country, state, city, zipcode, near_me, by_venue]):
            items_query = LostItem.objects()
        else:
            # Combine all conditions
            combined_query = query_conditions[0] if query_conditions else Q()
            for condition in query_conditions[1:]:
                combined_query = combined_query & condition
            items_query = LostItem.objects(combined_query)
        
        # Log query for debugging
        current_app.logger.info(f"Search query conditions count: {len(query_conditions)}")
        
        # Execute search with pagination
        skip = (page - 1) * per_page
        
        # Get total count for pagination
        total_items = items_query.count()
        total_pages = math.ceil(total_items / per_page)
        
        # Log results for debugging
        current_app.logger.info(f"Found {total_items} items for search")
        
        # Get paginated results
        items = items_query.skip(skip).limit(per_page).order_by('-created_at')
        
        # Format results
        results = []
        for item in items:
            result = {
                'id': str(item.id),
                'slug': encode_object_id(str(item.id)),
                'title': getattr(item, 'title', 'Untitled'),
                'description': item.specific_description if hasattr(item, 'specific_description') else '',
                'status': item.status,
                'category': item.category,
                'sub_category': item.sub_category,
                'country': item.country,
                'state': item.state_province if hasattr(item, 'state_province') else '',
                'city': item.city_town if hasattr(item, 'city_town') else '',
                'zipcode': item.zipcode,
                'location_description': item.specific_location if hasattr(item, 'specific_location') else '',
                'created_at': item.created_at.isoformat() if item.created_at else None,
                'image_url': get_item_image_url(item),
                'reporter_name': get_reporter_name(item.reported_by) if item.reported_by else 'Unknown'
            }
            results.append(result)
        
        return jsonify({
            'status': 'success',
            'results': results,
            'page': page,
            'total_pages': total_pages,
            'total_items': total_items,
            'per_page': per_page
        }), 200
        
    except AppError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), e.status_code
    
    except Exception as e:
        # Log the actual error for debugging
        current_app.logger.error(f"Search error: {str(e)}\n{traceback.format_exc()}")
        
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

def add_radius_search(query, zipcode, radius_km):
    """
    Add radius search around a zipcode
    Note: This is a simplified implementation. 
    For production, you'd want to use a proper geospatial database.
    """
    # This is a placeholder implementation
    # In a real application, you'd use MongoDB's geospatial queries
    # with proper coordinates and $geoWithin operators
    
    # For now, we'll just search by zipcode with a note
    query['zipcode'] = {'$regex': zipcode, '$options': 'i'}
    return query

def add_location_radius_search(query, location, radius_km):
    """
    Add radius search around user location
    """
    # This is a placeholder implementation
    # In a real application, you'd use proper geospatial queries
    return query

def get_item_image_url(item):
    """
    Get the image URL for an item
    """
    if hasattr(item, 'images') and item.images and len(item.images) > 0:
        # Return the first image URL
        return f"/uploads/{item.images[0]}"
    return None

def get_reporter_name(reporter):
    """
    Get the reporter's name for display
    """
    try:
        # reporter can be either a ReferenceField object or an ID
        if hasattr(reporter, 'first_name'):
            # It's already the user object
            return f"{reporter.first_name} {reporter.last_name}".strip()
        else:
            # It's an ID, fetch the user
            user = User.objects(id=str(reporter)).first()
            if user:
                return f"{user.first_name} {user.last_name}".strip()
        return "Unknown"
    except:
        return "Unknown"
