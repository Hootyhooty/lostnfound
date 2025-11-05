from flask import Blueprint
from Controllers.searchController import search_items

# ----------------------------
# Search routes
# ----------------------------
search_routes = Blueprint('search_routes', __name__, url_prefix='/api/v1')

# Search endpoint
search_routes.add_url_rule('/search', view_func=search_items, methods=['POST'])

@search_routes.route('/search', methods=['GET'])
def handle_search_get():
    """Prevent 404 spam from accidental GETs"""
    return '', 204
