import jwt
import hashlib
import secrets
import os
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app, render_template, make_response
from mongoengine import ValidationError

from Models.userModel import User
from Utils.appError import AppError
from Utils.jwt_utils import create_access_token, create_refresh_token, decode_token
from Utils.auth_decorator import token_required, roles_required
from werkzeug.security import generate_password_hash
from Utils.email import send_reset_email

auth_bp = Blueprint("auth", __name__)

JWT_SECRET = os.getenv("JWT_SECRET", "default_secret")
JWT_ALGORITHM = "HS256"

logger = logging.getLogger(__name__)

# =====================================================
# REGISTER
# =====================================================
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")
    password_confirm = data.get("password_confirm")

    if not all([name, email, phone,password, password_confirm]):
        raise AppError("All fields are required.", 400)

    if password != password_confirm:
        raise AppError("Passwords do not match.", 400)

    if User.objects(email=email).first():
        raise AppError("Email already registered.", 400)
    if User.objects(phone=phone).first():
        raise AppError("Phone number already registered.", 400)

    try:
        # ✅ Create new user with default photo
        user = User(
            name=name,
            email=email,
            phone=int(phone),
            password=password,
            password_confirm=password_confirm,
            photo="default.jpg"  # <- default profile picture
        )
        user.save()

        logger.info(f"✅ New user registered: {email}/ {phone}")
        return jsonify({
            "success": True,
            "status": "success",
            "message": "User registered successfully.",
            "user": user.to_json()
        }), 201

    except ValidationError as e:
        raise AppError(str(e), 400)
    except Exception as e:
        logger.exception("🔥 Unexpected error during registration.")
        raise AppError("Internal server error.", 500)



# =====================================================
# LOGIN
# =====================================================
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    identifier = data.get("email") or data.get("identifier") or data.get("phone")
    password = data.get("password")

    if not identifier or not password:
        raise AppError("Email/Phone/Username and password are required.", 400)

    # Determine what type of identifier this is
    user = None
    if identifier.isdigit():  # Phone
        user = User.objects(phone=int(identifier)).first()
    elif "@" in identifier:  # Email
        user = User.objects(email=identifier.lower()).first()
    else:  # Username
        user = User.objects(name=identifier).first()

    if not user:
        raise AppError("User not found.", 404)
    if not user.correct_password(password):
        raise AppError("Invalid password.", 401)

    role_value = getattr(user.role, "value", user.role)
    access_token = create_access_token(user.id, role_value)
    refresh_token = create_refresh_token({"user_id": str(user.id), "role": role_value})

    logger.info(f"✅ Login successful for {identifier}")

    # Set HttpOnly cookies as well so navigation to protected views works without JS
    resp = make_response(jsonify({
        "success": True,
        "status": "success",
        "message": "Login successful.",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token": access_token,  # For backward compatibility
        "user": user.to_json()
    }))
    # Cookie options
    cookie_kwargs = {
        "httponly": True,
        "samesite": "Lax",
        "secure": False  # set True when using HTTPS
    }
    resp.set_cookie("access_token", access_token, **cookie_kwargs)
    resp.set_cookie("refresh_token", refresh_token, **cookie_kwargs)
    return resp, 200


# =====================================================
# REFRESH TOKEN
# =====================================================
@auth_bp.route("/refresh", methods=["POST"])
def refresh_token():
    data = request.get_json() or {}
    token = data.get("refresh_token")

    if not token:
        raise AppError("Refresh token required.", 400)

    decoded = decode_token(token)
    if not decoded:
        raise AppError("Invalid or expired refresh token.", 401)

    user = User.objects(id=decoded.get("user_id")).first()
    if not user:
        raise AppError("User not found.", 404)

    new_access_token = create_access_token(user.id, user.role.value)
    logger.info(f"🔁 Token refreshed for {user.email}")

    resp = make_response(jsonify({
        "status": "success",
        "access_token": new_access_token
    }))
    cookie_kwargs = {
        "httponly": True,
        "samesite": "Lax",
        "secure": False
    }
    resp.set_cookie("access_token", new_access_token, **cookie_kwargs)
    return resp, 200


# =====================================================
# FORGOT PASSWORD
# =====================================================
@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()

    if not email:
        raise AppError("Email is required.", 400)

    user = User.objects(email=email).first()
    if not user:
        logger.warning(f"⚠️ Forgot password attempted for non-existent user: {email}")
        # Always return success to prevent email enumeration attacks
        return jsonify({
            "success": True,
            "status": "success",
            "message": "If an account with that email exists, a reset link has been sent."
        }), 200

    reset_token = jwt.encode(
        {"user_id": str(user.id), "exp": datetime.utcnow() + timedelta(minutes=15)},
        key=JWT_SECRET,
        algorithm="HS256"
    )

    reset_url = f"http://localhost:5000/reset-password?token={reset_token}"
    logger.info(f"🔑 Password reset link for {email}: {reset_url}")

    # Optional email sending
 #   try:
 #       send_reset_email(user.email, reset_url)
 #   except Exception as e:
 #       logger.warning(f"📧 Email send failed (dev mode): {str(e)}")

    return jsonify({
        "success": True,
        "status": "success",
        "message": "Password reset link sent (check logs for dev mode)."
    }), 200


# =====================================================
# RESET PASSWORD
# =====================================================
@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json() or {}
    token = data.get("token")
    new_password = data.get("password")

    if not token or not new_password:
        raise AppError("Missing token or password.", 400)

    try:
        decoded = jwt.decode(token, current_app.config.get("JWT_SECRET"), algorithms=["HS256"])
        user_id = decoded.get("user_id")
    except jwt.ExpiredSignatureError:
        raise AppError("Reset token expired. Please request a new one.", 400)
    except jwt.InvalidTokenError:
        raise AppError("Invalid reset token.", 400)

    user = User.objects(id=user_id).first()
    if not user:
        raise AppError("User not found.", 404)

    user.password = User.hash_password(new_password)
    user.save()

    logger.info(f"🔐 Password reset successfully for {user.email}")
    return jsonify({"success": True, "status": "success", "message": "Password reset successfully."}), 200


# =====================================================
# CURRENT USER
# =====================================================
@auth_bp.route("/me", methods=["GET"])
@token_required
def get_current_user(user):
    logger.debug(f"👤 Current user accessed: {user.email}")
    return jsonify({"success": True, "status": "success", "user": user.to_json()}), 200


# =====================================================
# ADMIN DASHBOARD
# =====================================================
@auth_bp.route("/admin/dashboard", methods=["GET"])
@roles_required("admin")
def admin_dashboard(user):
    logger.info(f"🛠 Admin dashboard accessed by {user.email}")
    return jsonify({
        "status": "success",
        "message": f"Welcome Admin {user.name}!",
        "data": {
            "user_count": User.objects.count(),
            "active_users": User.objects(active=True).count(),
        }
    }), 200


# =====================================================
# LOGOUT
# =====================================================
@auth_bp.route("/logout", methods=["POST"])
def logout():
    logger.info("👋 User logged out (client-side).")
    return jsonify({"status": "success", "message": "Logout successful."}), 200


@auth_bp.errorhandler(AppError)
def handle_app_error(e):
    response = jsonify({
        "success": False,
        "status": "error",
        "message": str(e)
    })
    response.status_code = e.status_code
    return response


@auth_bp.errorhandler(500)
def handle_500(e):
    return jsonify({
        "success": False,
        "status": "error",
        "message": "Internal server error."
    }), 500