from flask import Blueprint
from Controllers.lostItemController import (
    create_lost_item, get_user_lost_items, get_lost_item_by_id, 
    update_lost_item, delete_lost_item, claim_lost_item
)

# ----------------------------
# Lost Item API routes
# ----------------------------
lost_item_routes = Blueprint('lost_item_routes', __name__, url_prefix='/api/v1/lost-items')

# Lost item CRUD operations
lost_item_routes.add_url_rule('', view_func=create_lost_item, methods=['POST'])
lost_item_routes.add_url_rule('', view_func=get_user_lost_items, methods=['GET'])
lost_item_routes.add_url_rule('/<item_id>', view_func=get_lost_item_by_id, methods=['GET'])
lost_item_routes.add_url_rule('/<item_id>', view_func=update_lost_item, methods=['PUT'])
lost_item_routes.add_url_rule('/<item_id>', view_func=delete_lost_item, methods=['DELETE'])
lost_item_routes.add_url_rule('/<item_id>/claim', view_func=claim_lost_item, methods=['POST'])
