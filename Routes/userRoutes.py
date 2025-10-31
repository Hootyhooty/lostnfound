from flask import Blueprint
from Controllers.authController import login, register, logout
from Controllers.userController import (
    upload_image_to_all_imgs,
    upload_default_image_to_all_imgs,
    get_image_from_all_imgs, get_me, update_profile, deactivate_account
)

# ----------------------------
# Blueprints
# ----------------------------
auth_routes = Blueprint('auth_routes', __name__, url_prefix='/api/v1/auth')
user_routes = Blueprint('user_routes', __name__, url_prefix='/api/v1/users')

# ----------------------------
# Auth routes
# ----------------------------
auth_routes.add_url_rule('/login', view_func=login, methods=['POST'])
auth_routes.add_url_rule('/register', view_func=register, methods=['POST'])
auth_routes.add_url_rule('/logout', view_func=logout, methods=['POST'])

# ----------------------------
# User (AllImgs) routes
# ----------------------------
user_routes.add_url_rule('/upload-image-to-allimgs', view_func=upload_image_to_all_imgs, methods=['POST'])
user_routes.add_url_rule('/upload-default-to-allimgs', view_func=upload_default_image_to_all_imgs, methods=['POST'])
user_routes.add_url_rule('/me', view_func=get_me, methods=['GET'])
user_routes.add_url_rule('/profile', view_func=update_profile, methods=['PUT'])
user_routes.add_url_rule('/deactivate', view_func=deactivate_account, methods=['POST'])

# ✅ Serve images from all_imgs (GridFS)
user_routes.add_url_rule('/uploads/<filename>', view_func=get_image_from_all_imgs, methods=['GET'])
