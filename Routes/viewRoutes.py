from flask import Blueprint
from Controllers.viewController import home, about, blog, testimonial, profile, edit_profile, report_lost_item, shop, \
    search_results, item_detail, edit_lost_item

view_routes = Blueprint('view_routes', __name__)

view_routes.add_url_rule('/', view_func=home, methods=['GET'])
view_routes.add_url_rule('/about', view_func=about, methods=['GET'])
view_routes.add_url_rule('/blog', view_func=blog, methods=['GET'])
view_routes.add_url_rule('/testimonial', view_func=testimonial, methods=['GET'])
view_routes.add_url_rule('/profile/<slug>', view_func=profile, methods=['GET'])  # ✅ fixed slug
view_routes.add_url_rule('/profile/edit', view_func=edit_profile, methods=['GET'])
view_routes.add_url_rule('/report-lost-found', view_func=report_lost_item, methods=['GET'])
view_routes.add_url_rule('/shop', view_func=shop, methods=['GET'])
view_routes.add_url_rule('/search_results', view_func=search_results, methods=['GET'])
view_routes.add_url_rule('/item/<slug>', view_func=item_detail, methods=['GET'])
view_routes.add_url_rule('/item/<slug>/edit', view_func=edit_lost_item, methods=['GET'])