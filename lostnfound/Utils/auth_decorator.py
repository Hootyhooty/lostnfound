# Utils/auth_decorator.py
from functools import wraps
from flask import request, jsonify, render_template, redirect
from Utils.jwt_utils import decode_token
from Models.userModel import User
from enum import Enum


def token_required(f):
    """Ensure that a valid JWT is present.
    Returns JSON for API requests, redirects to error page for HTML requests."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        token = None

        # Prefer Authorization header if present and well-formed
        if auth_header:
            try:
                token_type, token_val = auth_header.split(" ")
                if token_type.lower() == "bearer" and token_val:
                    token = token_val
            except ValueError:
                pass

        # Fallback to cookies
        if not token:
            token = request.cookies.get("access_token")

        # Check if this is an API request
        is_api_request = (request.path.startswith("/api") or 
                          request.accept_mimetypes.best == "application/json" or
                          request.headers.get('Content-Type') == 'application/json')

        if not token:
            if is_api_request:
                return jsonify({"success": False, "message": "Authorization token missing"}), 401
            else:
                return render_template("error.html",
                                     error_code=401,
                                     error_message="Authentication required. Please log in to access this page."), 401

        decoded = decode_token(token)
        if not decoded:
            if is_api_request:
                return jsonify({"success": False, "message": "Invalid or expired token"}), 401
            else:
                return render_template("error.html",
                                     error_code=401,
                                     error_message="Your session has expired. Please log in again."), 401

        user = User.objects(id=decoded.get("user_id")).first()
        if not user:
            if is_api_request:
                return jsonify({"success": False, "message": "User not found"}), 404
            else:
                return render_template("error.html",
                                     error_code=404,
                                     error_message="User not found."), 404

        # Attach user to the wrapped function
        return f(user, *args, **kwargs)

    return decorated


def roles_required(*allowed_roles):
    """
    Restrict access to users with specific roles.
    Returns JSON for API requests, redirects to error page for HTML requests.
    Example:
        @auth_bp.route("/admin/dashboard")
        @roles_required("admin")
        def admin_dashboard(user): ...
    """
    def wrapper(f):
        @wraps(f)
        @token_required
        def decorated(user, *args, **kwargs):
            user_role = getattr(user.role, "value", user.role)
            if user_role not in allowed_roles:
                # Check if this is an HTML request (not API)
                is_api_request = (request.path.startswith("/api") or 
                                  request.accept_mimetypes.best == "application/json" or
                                  request.headers.get('Content-Type') == 'application/json')
                
                if is_api_request:
                    return jsonify({
                        "success": False,
                        "message": f"Access denied. Requires role(s): {', '.join(allowed_roles)}"
                    }), 403
                else:
                    # Redirect to error page for unauthorized access
                    return render_template("error.html",
                                         error_code=403,
                                         error_message="Access Denied. You do not have permission to access this page."), 403

            return f(user, *args, **kwargs)

        return decorated
    return wrapper
