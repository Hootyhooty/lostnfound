from flask import Blueprint
from Controllers.adminController import (
    admin_logs, get_logs_json,
    admin_dashboard_page,
    admin_users_api, admin_user_delete,
    admin_items_api, admin_item_delete,
    admin_testimonials_api, admin_testimonial_delete,
    admin_send_email
)
from Controllers.salesController import create_sale

admin_routes = Blueprint("admin_routes", __name__)

# Admin dashboards
admin_routes.add_url_rule("/admin", view_func=admin_dashboard_page, methods=["GET"])
admin_routes.add_url_rule("/admin/logs", view_func=admin_logs, methods=["GET"])

# Optional: JSON endpoint for async data loading
admin_routes.add_url_rule("/admin/logs/data", view_func=get_logs_json, methods=["GET"])

admin_routes.add_url_rule('/sales', view_func=create_sale, methods=['POST'])

# Admin APIs
admin_routes.add_url_rule('/admin/api/users', view_func=admin_users_api, methods=['GET', 'POST'])
admin_routes.add_url_rule('/admin/api/users/<user_id>', view_func=admin_user_delete, methods=['DELETE'])
admin_routes.add_url_rule('/admin/api/items', view_func=admin_items_api, methods=['GET'])
admin_routes.add_url_rule('/admin/api/items/<item_id>', view_func=admin_item_delete, methods=['DELETE'])
admin_routes.add_url_rule('/admin/api/testimonials', view_func=admin_testimonials_api, methods=['GET'])
admin_routes.add_url_rule('/admin/api/testimonials/<tid>', view_func=admin_testimonial_delete, methods=['DELETE'])
admin_routes.add_url_rule('/admin/api/send-email', view_func=admin_send_email, methods=['POST'])
