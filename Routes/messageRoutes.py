from flask import Blueprint
from Controllers.messageController import create_message, get_inbox, mark_read, reply_message

message_routes = Blueprint('message_routes', __name__, url_prefix='/api/v1')

message_routes.add_url_rule('/messages', view_func=create_message, methods=['POST'])
message_routes.add_url_rule('/messages/inbox', view_func=get_inbox, methods=['GET'])
message_routes.add_url_rule('/messages/<message_id>/read', view_func=mark_read, methods=['PATCH'])
message_routes.add_url_rule('/messages/reply', view_func=reply_message, methods=['POST'])


