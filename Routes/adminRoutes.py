from flask import Blueprint
from Controllers.adminController import admin_logs, get_logs_json
from Controllers.salesController import create_sale

admin_routes = Blueprint("admin_routes", __name__)

# Admin dashboard
admin_routes.add_url_rule("/admin/logs", view_func=admin_logs, methods=["GET"])

# Optional: JSON endpoint for async data loading
admin_routes.add_url_rule("/admin/logs/data", view_func=get_logs_json, methods=["GET"])

admin_routes.add_url_rule('/sales', view_func=create_sale, methods=['POST'])
