from flask import render_template, flash, Blueprint, current_app, request

error_bp = Blueprint('errors', __name__)

@error_bp.app_errorhandler(404)
def not_found_error(e):
    # Skip logging for common development requests
    skip_logging_paths = [
        '/.well-known/appspecific/com.chrome.devtools.json',
        '/favicon.ico',
        '/robots.txt'
    ]
    
    if request.path not in skip_logging_paths:
        flash("The page you requested could not be found.", "warning")
        
        # Log with request context
        current_app.logger.warning(
            f"404 Not Found: {e} | URL: {request.url} | Method: {request.method} | IP: {request.remote_addr}"
        )

    return render_template('error.html',
                           error_code=404,
                           error_message="Page Not Found"), 404


@error_bp.app_errorhandler(500)
def internal_error(e):
    flash("Something went wrong. Please try again later.", "error")

    current_app.logger.error(
        f"500 Internal Server Error: {e} | URL: {request.url} | Method: {request.method} | IP: {request.remote_addr}",
        exc_info=True
    )

    return render_template('error.html',
                           error_code=500,
                           error_message="Internal Server Error"), 500


@error_bp.app_errorhandler(Exception)
def handle_unexpected_error(e):
    flash("An unexpected error occurred. Please try again later.", "error")

    # This includes traceback automatically
    current_app.logger.exception(
        f"Unexpected Application Error: {e} | URL: {request.url} | Method: {request.method} | IP: {request.remote_addr}"
    )

    return render_template('error.html',
                           error_code=500,
                           error_message="Unexpected Application Error"), 500
