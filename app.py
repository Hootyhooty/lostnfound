import os
import logging
from logging.handlers import TimedRotatingFileHandler,RotatingFileHandler, SMTPHandler

import timedelta
from flask import Flask, send_from_directory, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
# Removed SQLAlchemy and Migrate - using MongoDB instead
from datetime import datetime
from collections import defaultdict

# Import blueprints
from Controllers.authController import auth_bp
from Controllers.errorController import error_bp
from Routes.adminRoutes import admin_routes
from Routes.viewRoutes import view_routes
from Routes.userRoutes import user_routes, auth_routes
from Routes.lostItemRoutes import lost_item_routes
from Routes.searchRoutes import search_routes
from Routes.messageRoutes import message_routes
from Routes.testimonialRoutes import api_testimonial_routes
from Utils.appError import AppError

#initialize database first
from Utils.db import init_db
init_db()

# ----------------------------
# Flask app configuration
# ----------------------------
app = Flask(__name__, template_folder='Templates', static_folder='.', static_url_path='')
app.config['SECRET_KEY'] = 'your_secret_key'
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")
app.config['JWT_SECRET'] = os.getenv("JWT_SECRET", "super_jwt_secret")
#app.permanent_session_lifetime = timedelta(hours=2)

# ----------------------------
# Rate Limiter
# ----------------------------
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[
        os.getenv("LIMIT_DEFAULT_HOURLY", "200 per hour"),
        os.getenv("LIMIT_DEFAULT_SECONDLY", "10 per second")
    ],
)

# Serve CSS from Templates/css
@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('Templates/css', filename)

# Handle CSS map files specifically
@app.route('/css/<path:filename>.map')
def serve_css_map(filename):
    try:
        return send_from_directory('Templates/css', f'{filename}.map')
    except Exception:
        # Return empty response for missing map files to prevent 404 errors
        return '', 204

# Handle Chrome DevTools requests
@app.route('/.well-known/appspecific/com.chrome.devtools.json')
def chrome_devtools():
    return '', 204

# Handle other common development requests
@app.route('/favicon.ico')
def favicon():
    try:
        return send_from_directory('images', 'lf2.ico')
    except Exception:
        return '', 204

# Handle robots.txt
@app.route('/robots.txt')
def robots_txt():
    return """User-agent: *
Allow: /
Disallow: /api/
Disallow: /admin/
""", 200, {'Content-Type': 'text/plain'}

# Serve JS from js/
@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('js', filename)

# Serve images from images/
@app.route('/images/<path:filename>')
def serve_images(filename):
    return send_from_directory('images', filename)

# Serve fonts from Templates/fonts and root fonts/
@app.route('/fonts/<path:filename>')
def serve_fonts(filename):
    # Try Templates/fonts first, then root fonts
    try:
        return send_from_directory('Templates/fonts', filename)
    except Exception:
        return send_from_directory('fonts', filename)

# ----------------------------
# Register blueprints
# ----------------------------
app.register_blueprint(error_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(view_routes)
app.register_blueprint(admin_routes)
app.register_blueprint(auth_routes)
app.register_blueprint(user_routes)
app.register_blueprint(lost_item_routes)
app.register_blueprint(search_routes)
app.register_blueprint(message_routes)
app.register_blueprint(api_testimonial_routes)


# ----------------------------
# Logging Configuration
# ----------------------------
from Utils.logger import setup_logging
setup_logging(app)

# ----------------------------
#   Global Error Handlers
# ----------------------------
from flask import render_template

@app.errorhandler(AppError)
def handle_app_error(err):
    """
    Handles custom AppError exceptions for API and web routes.
    """
    # If request is from an API route or expects JSON → return JSON
    if (request.path.startswith("/api") or 
        request.path.startswith("/register") or 
        request.path.startswith("/login") or 
        request.path.startswith("/logout") or 
        request.path.startswith("/me") or 
        request.accept_mimetypes.best == "application/json" or
        request.headers.get('Content-Type') == 'application/json'):
        app.logger.warning(f"AppError {err.status_code} at {request.path}: {err}")
        response = {
            "status": err.status,
            "message": str(err)
        }
        return jsonify(response), err.status_code

    # Otherwise render an HTML error page
    return render_template("error.html",
                           error_code=err.status_code,
                           error_message=str(err)), err.status_code


@app.errorhandler(Exception)
def handle_unexpected_error(err):
    """
    Catch-all for unexpected server errors.
    """
    app.logger.exception(f"Unexpected error: {err} | Path: {request.path}")

    # API or JSON request
    if (request.path.startswith("/api") or 
        request.path.startswith("/register") or 
        request.path.startswith("/login") or 
        request.path.startswith("/logout") or 
        request.path.startswith("/me") or 
        request.accept_mimetypes.best == "application/json" or
        request.headers.get('Content-Type') == 'application/json'):
        return jsonify({
            "status": "error",
            "message": "Something went wrong on the server."
        }), 500

    # Webpage request
    return render_template("error.html",
                           error_code=500,
                           error_message="Internal Server Error"), 500

# ----------------------------
#   Rate Limit Error Handler
# ----------------------------
@app.errorhandler(429)
def ratelimit_handler(err):
    if (request.path.startswith("/api") or 
        request.path.startswith("/register") or 
        request.path.startswith("/login") or 
        request.path.startswith("/logout") or 
        request.path.startswith("/me") or 
        request.accept_mimetypes.best == "application/json" or
        request.headers.get('Content-Type') == 'application/json'):
        return jsonify({
            "status": "fail",
            "message": "Rate limit exceeded. Please slow down."
        }), 429
    return render_template("error.html",
                           error_code=429,
                           error_message="Too Many Requests"), 429

@app.route("/uploads/<filename>")
def get_uploaded_image(filename):
    from Models.allImgsModel import AllImgs
    from Utils.appError import AppError
    import io
    from flask import send_file

    img_doc = AllImgs.objects(filename=filename).first()
    if not img_doc:
        raise AppError("Image not found", 404)

    gridout = img_doc.file.get()
    return send_file(
        io.BytesIO(gridout.read()),
        mimetype=img_doc.content_type or "image/jpeg"
    )


# ----------------------------
# Run the app
# ----------------------------
if __name__ == '__main__':
    port = int(os.getenv('PORT', 4000))
    print(f"App running on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)