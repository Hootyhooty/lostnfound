from flask import Blueprint
from Controllers.adminController import (
    admin_logs, get_logs_json, get_logs_text,
    admin_dashboard_page,
    admin_users_api, admin_user_delete, admin_user_toggle_active,
    admin_items_api, admin_item_delete, admin_item_toggle_active,
    admin_testimonials_api, admin_testimonial_delete, admin_testimonial_toggle_public,
    admin_send_email
)
from Controllers.salesController import create_sale, create_stripe_checkout, paypal_create_order, paypal_return, stripe_success, stripe_webhook, receipt_view

admin_routes = Blueprint("admin_routes", __name__)

# Admin dashboards
admin_routes.add_url_rule("/admin", view_func=admin_dashboard_page, methods=["GET"])
admin_routes.add_url_rule("/admin/logs", view_func=admin_logs, methods=["GET"])

# Optional: JSON endpoint for async data loading
admin_routes.add_url_rule("/admin/logs/data", view_func=get_logs_json, methods=["GET"])
admin_routes.add_url_rule("/admin/logs/text", view_func=get_logs_text, methods=["GET"])

admin_routes.add_url_rule('/sales', view_func=create_sale, methods=['POST'])
admin_routes.add_url_rule('/api/v1/sales', view_func=create_sale, methods=['POST'])
admin_routes.add_url_rule('/api/checkout/stripe', view_func=create_stripe_checkout, methods=['POST'])
admin_routes.add_url_rule('/api/paypal/create-order', view_func=paypal_create_order, methods=['POST'])
admin_routes.add_url_rule('/paypal/return', view_func=paypal_return, methods=['GET'])
admin_routes.add_url_rule('/stripe/success', view_func=stripe_success, methods=['GET'])
admin_routes.add_url_rule('/webhook', view_func=stripe_webhook, methods=['POST'])
admin_routes.add_url_rule('/receipt/<sale_id>', view_func=receipt_view, methods=['GET'])

# Admin APIs
admin_routes.add_url_rule('/admin/api/users', view_func=admin_users_api, methods=['GET', 'POST'])
admin_routes.add_url_rule('/admin/api/users/<user_id>', view_func=admin_user_delete, methods=['DELETE'])
admin_routes.add_url_rule('/admin/api/users/<user_id>/toggle', view_func=admin_user_toggle_active, methods=['POST'])
admin_routes.add_url_rule('/admin/api/items', view_func=admin_items_api, methods=['GET'])
admin_routes.add_url_rule('/admin/api/items/<item_id>', view_func=admin_item_delete, methods=['DELETE'])
admin_routes.add_url_rule('/admin/api/items/<item_id>/toggle', view_func=admin_item_toggle_active, methods=['POST'])
admin_routes.add_url_rule('/admin/api/testimonials', view_func=admin_testimonials_api, methods=['GET'])
admin_routes.add_url_rule('/admin/api/testimonials/<tid>', view_func=admin_testimonial_delete, methods=['DELETE'])
admin_routes.add_url_rule('/admin/api/testimonials/<tid>/toggle', view_func=admin_testimonial_toggle_public, methods=['POST'])
admin_routes.add_url_rule('/admin/api/send-email', view_func=admin_send_email, methods=['POST'])
