import os
import logging
from logging.handlers import TimedRotatingFileHandler, SMTPHandler
import gzip
import glob
import time
import re
from datetime import datetime
from collections import defaultdict
import click
from flask.cli import with_appcontext


# ==================================================
# LOGGING SETUP
# ==================================================
def setup_logging(app):
    """Configure logging for the Flask app."""
    os.makedirs("logs", exist_ok=True)

    # Prevent duplicate log handlers when Flask auto-reloads
    if getattr(app, "_logging_configured", False):
        return
    app._logging_configured = True

    # -------------------------
    # FORMATTERS
    # -------------------------
    log_format = "%(asctime)s [%(levelname)s] in %(module)s: %(message)s"
    formatter = logging.Formatter(log_format)

    # -------------------------
    # FILE HANDLERS
    # -------------------------
    app_handler = TimedRotatingFileHandler(
        "logs/app.log", when="midnight", interval=1, backupCount=14,
        encoding="utf-8", delay=True
    )
    app_handler.suffix = "%Y-%m-%d"
    app_handler.setFormatter(formatter)
    app_handler.setLevel(logging.INFO)

    error_handler = TimedRotatingFileHandler(
        "logs/error.log", when="midnight", interval=1, backupCount=30,
        encoding="utf-8", delay=True
    )
    error_handler.suffix = "%Y-%m-%d"
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)

    access_handler = TimedRotatingFileHandler(
        "logs/access.log", when="midnight", interval=1, backupCount=7,
        encoding="utf-8", delay=True
    )
    access_handler.suffix = "%Y-%m-%d"
    access_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    access_handler.setLevel(logging.INFO)

    # -------------------------
    # CONSOLE HANDLER (DEV MODE)
    # -------------------------
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # -------------------------
    # REGISTER LOGGERS
    # -------------------------
    app_logger = app.logger
    app_logger.setLevel(logging.INFO)
    app_logger.addHandler(app_handler)
    app_logger.addHandler(error_handler)
    app_logger.addHandler(console_handler)

    access_logger = logging.getLogger("access")
    access_logger.setLevel(logging.INFO)
    access_logger.addHandler(access_handler)
    # Dedicated sales logger
    sales_handler = TimedRotatingFileHandler(
        "logs/sales.log", when="midnight", interval=1, backupCount=30,
        encoding="utf-8", delay=True
    )
    sales_handler.suffix = "%Y-%m-%d"
    sales_handler.setFormatter(formatter)
    sales_handler.setLevel(logging.INFO)
    sales_logger = logging.getLogger("sales")
    sales_logger.setLevel(logging.INFO)
    sales_logger.addHandler(sales_handler)
    # Mirror to console for platform logs
    sales_console = logging.StreamHandler()
    sales_console.setFormatter(formatter)
    sales_console.setLevel(logging.INFO)
    sales_logger.addHandler(sales_console)
    # Mirror access logs to console so Render captures them
    access_console = logging.StreamHandler()
    access_console.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    access_console.setLevel(logging.INFO)
    access_logger.addHandler(access_console)

    # -------------------------
    # EMAIL ALERTS (OPT-IN)
    # -------------------------
    enable_smtp = os.getenv("ENABLE_SMTP_ALERTS", "false").lower() in ("1", "true", "yes")
    if enable_smtp and not app.debug:
        try:
            mail_handler = SMTPHandler(
                mailhost=(os.getenv("SMTP_HOST", "smtp.gmail.com"), int(os.getenv("SMTP_PORT", "587"))),
                fromaddr=os.getenv("SMTP_FROM", "noreply@yourapp.com"),
                toaddrs=[addr.strip() for addr in os.getenv("SMTP_TO", "admin@yourapp.com").split(",") if addr.strip()],
                subject=os.getenv("SMTP_SUBJECT", "🚨 Lost&Found Critical Error"),
                credentials=(os.getenv("SMTP_USER", "your_email@gmail.com"), os.getenv("SMTP_PASS", "your_app_password")),
                secure=()
            )
            mail_handler.setLevel(logging.ERROR)
            mail_handler.setFormatter(formatter)
            app_logger.addHandler(mail_handler)
        except Exception as e:
            app_logger.warning(f"SMTP alerts disabled due to configuration error: {e}")

    # -------------------------
    # LOG HOOKS & TASKS
    # -------------------------
    register_access_log_hook(app, access_logger)
    register_cleanup_task(app)
    register_log_summary_command(app)

    app_logger.info("🚀 Logging initialized successfully.")
    return app_logger


# ==================================================
# ACCESS LOGGING
# ==================================================
def register_access_log_hook(app, access_logger):
    """Logs each incoming request (IP, method, URL) into access.log."""
    from flask import request

    @app.before_request
    def log_request_info():
        try:
            access_logger.info(f"{request.remote_addr} {request.method} {request.url}")
        except Exception as e:
            app.logger.warning(f"⚠️ Failed to log request: {e}")


# ==================================================
# OLD LOG CLEANUP & COMPRESSION
# ==================================================
def register_cleanup_task(app):
    """Compress old logs and delete logs older than 7 days."""
    def cleanup_old_logs(folder="logs", days=7):
        now = time.time()
        for log_file in glob.glob(f"{folder}/*.log.*"):
            if not log_file.endswith(".gz"):
                # Compress rotated logs
                try:
                    with open(log_file, "rb") as f_in:
                        with gzip.open(f"{log_file}.gz", "wb") as f_out:
                            f_out.writelines(f_in)
                    os.remove(log_file)
                    app.logger.info(f"🗜️ Compressed log: {log_file}")
                except Exception as e:
                    app.logger.error(f"❌ Failed to compress {log_file}: {e}")

        # Delete .gz files older than X days
        for gz_file in glob.glob(f"{folder}/*.gz"):
            if os.stat(gz_file).st_mtime < now - days * 86400:
                os.remove(gz_file)
                app.logger.info(f"🧹 Deleted old log: {gz_file}")

    cleanup_old_logs()


# ==================================================
# CLI LOG SUMMARY COMMAND
# ==================================================
def register_log_summary_command(app):
    """Adds 'flask logs:summary' CLI command to view log stats."""
    LOG_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2}).*\[(INFO|ERROR|WARNING)\]")

    @click.command("logs:summary")
    @with_appcontext
    @click.option("--days", default=7, help="Days of logs to summarize")
    def summarize_logs(days):
        log_dir = "logs"
        summary = defaultdict(lambda: {"INFO": 0, "ERROR": 0, "WARNING": 0})
        now = datetime.now()

        for filename in os.listdir(log_dir):
            if not filename.startswith(("app.log", "error.log")):
                continue

            path = os.path.join(log_dir, filename)
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            if (now - mtime).days > days:
                continue

            opener = gzip.open if filename.endswith(".gz") else open
            try:
                with opener(path, "rt", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        match = LOG_PATTERN.match(line)
                        if match:
                            date_str, level = match.groups()
                            summary[date_str][level] += 1
            except Exception as e:
                click.echo(f"⚠️ Could not read {filename}: {e}")

        if not summary:
            click.echo("No log entries found in the specified time range.")
            return

        click.echo("\n📊 Log Summary\n──────────────────────────────")
        total_info = total_error = total_warn = 0

        for date_str in sorted(summary.keys()):
            counts = summary[date_str]
            total_info += counts["INFO"]
            total_error += counts["ERROR"]
            total_warn += counts["WARNING"]
            click.echo(
                f"{date_str}  INFO: {counts['INFO']:<5}  WARNING: {counts['WARNING']:<5}  ERROR: {counts['ERROR']:<5}"
            )

        click.echo("──────────────────────────────")
        click.echo(
            f"Total INFO: {total_info}   WARNING: {total_warn}   ERROR: {total_error}"
        )

    app.cli.add_command(summarize_logs)
