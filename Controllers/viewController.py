import logging
from flask import render_template, Blueprint
from Models.userModel import User
from Utils.appError import AppError
from Models.lostItemModel import LostItem
from Models.messageModel import Message
from Utils.hashid_utils import decode_slug, encode_object_id
from Utils.auth_decorator import token_required

logger = logging.getLogger(__name__)

# ✅ Create the blueprint here (so routes can be registered properly)
view_bp = Blueprint("view", __name__)

@view_bp.route("/")
def home():
    logger.info("Rendering home page")
    return render_template("index.html")

@view_bp.route("/about")
def about():
    return render_template("about.html")

@view_bp.route("/blog")
def blog():
    return render_template("blog.html")

@view_bp.route("/testimonial")
def testimonial():
    return render_template("testimonial.html")

# ✅ Profile route using slug instead of ID
@view_bp.route("/profile/<slug>")
@token_required
def profile(user, slug):
    target_user = User.objects(profile_slug=slug).first()
    if not target_user:
        raise AppError("User not found.", 404)

    # Allow only self or admin
    if str(user.id) != str(target_user.id) and user.role != "admin":
        raise AppError("Unauthorized access.", 403)

    # Fetch user's lost items
    from Models.lostItemModel import LostItem
    lost_items = LostItem.objects(reported_by=target_user, is_active=True).order_by('-created_at')
    
    # Convert ObjectIds to strings for template rendering
    for item in lost_items:
        item.id_str = str(item.id)
        try:
            item.slug = encode_object_id(item.id)
        except Exception:
            item.slug = item.id_str
    
    # Fetch inbox messages
    inbox = Message.objects(receiver=target_user).order_by('-created_at')
    return render_template("profile.html", user=target_user, lost_items=lost_items, inbox=inbox)

# ✅ Edit Profile route
@view_bp.route("/profile/edit")
@token_required
def edit_profile(user):
    return render_template("edit_profile.html", user=user)

# ✅ Report Lost Item route
@view_bp.route("/report-lost-found")
@token_required
def report_lost_item(user):
    return render_template("report_lost_item.html", user=user)

@view_bp.route("/shop")
def shop():
    return render_template("shop.html")

@view_bp.route('/results', methods=['GET'])
def search_results():
    return render_template('results.html')

# ✅ Item detail route by slug
@view_bp.route('/item/<slug>')
def item_detail(slug: str):
    object_id_hex = decode_slug(slug)
    if not object_id_hex:
        raise AppError("Invalid item link", 404)

    item = LostItem.objects(id=object_id_hex, is_active=True).first()
    if not item:
        raise AppError("Item not found", 404)

    return render_template('item_detail.html', item=item, slug=slug)

# ✅ Edit Lost Item route (owner only)
@view_bp.route('/item/<slug>/edit')
@token_required
def edit_lost_item(user, slug: str):
    object_id_hex = decode_slug(slug)
    if not object_id_hex:
        raise AppError("Invalid item link", 404)

    item = LostItem.objects(id=object_id_hex, is_active=True).first()
    if not item:
        raise AppError("Item not found", 404)

    # Only reporter (or admin) can edit
    if str(item.reported_by.id) != str(user.id) and getattr(user, 'role', None) != "admin":
        raise AppError("Unauthorized access.", 403)

    return render_template('edit_lost_item.html', item=item, slug=slug)