import os
import gzip
import re
from datetime import datetime, timedelta
from collections import defaultdict
from flask import render_template, flash, jsonify

LOG_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2}) .* \[(INFO|ERROR|WARNING)\]")

def parse_logs(days=7, level: str | None = None, start_date: str | None = None, end_date: str | None = None):
    log_dir = "logs"
    summary = defaultdict(lambda: {"INFO": 0, "ERROR": 0, "WARNING": 0})

    # Compute date boundaries
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=days)

    # Overrides if explicit dates provided (format YYYY-MM-DD)
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            pass
    if end_date:
        try:
            # Inclusive end date end of day
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            pass

    level_filter = {"INFO", "ERROR", "WARNING"}
    if level and level.upper() in level_filter:
        level_filter = {level.upper()}

    for filename in os.listdir(log_dir):
        if not filename.startswith(("app.log", "error.log")):
            continue

        path = os.path.join(log_dir, filename)
        # Skip files completely outside modified window for a quick pre-filter
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            if mtime < start_dt:
                continue
        except Exception:
            pass

        opener = gzip.open if filename.endswith(".gz") else open
        try:
            with opener(path, "rt", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    match = LOG_PATTERN.match(line)
                    if not match:
                        continue
                    date_str, lvl = match.groups()
                    if lvl not in level_filter:
                        continue
                    try:
                        line_dt = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        continue
                    if not (start_dt <= line_dt < end_dt):
                        continue
                    summary[date_str][lvl] += 1
        except Exception as e:
            print(f"⚠️ Could not read {filename}: {e}")

    return dict(sorted(summary.items()))


def admin_logs():
    try:
        summary = parse_logs(days=7)

        totals = {"INFO": 0, "ERROR": 0, "WARNING": 0}
        for counts in summary.values():
            for level, value in counts.items():
                totals[level] += value

        if not summary:
            flash("No logs found for the last 7 days.", "info")

        return render_template(
            "admin_logs.html",
            summary=summary,
            totals=totals
        )

    except Exception as e:
        flash(f"Error loading logs: {e}", "error")
        return render_template(
            "error.html",
            error_code=500,
            error_message="Error loading log dashboard"
        ), 500


def get_logs_json():
    """JSON endpoint for async dashboard data. Supports optional filters via query params.

    Query params:
      - days: int, default 7
      - level: one of INFO|WARNING|ERROR
      - start_date, end_date: YYYY-MM-DD (overrides days if provided)
    """
    try:
        from flask import request

        days_param = request.args.get("days", default="7")
        level_param = request.args.get("level")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        try:
            days = max(1, int(days_param))
        except (TypeError, ValueError):
            days = 7

        summary = parse_logs(days=days, level=level_param, start_date=start_date, end_date=end_date)

        totals = {"INFO": 0, "ERROR": 0, "WARNING": 0}
        for counts in summary.values():
            for lvl, value in counts.items():
                totals[lvl] += value

        return jsonify({"summary": summary, "totals": totals})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================
# Admin Dashboard and API
# =============================
def admin_dashboard_page():
    """Render the unified admin dashboard with sidebar navigation."""
    return render_template("admin_dashboard.html")


def _safe_obj_id(obj):
    try:
        return str(obj.id)
    except Exception:
        return None


def _serialize_user(u):
    return {
        "id": _safe_obj_id(u),
        "name": getattr(u, "name", ""),
        "email": getattr(u, "email", ""),
        "phone": getattr(u, "phone", None),
        "role": getattr(getattr(u, "role", None), "value", "user"),
        "active": getattr(u, "active", True),
        "profile_slug": getattr(u, "profile_slug", ""),
        "created_at": getattr(u, "password_changed_at", None),
    }


def admin_users_api():
    """GET: list users; POST: create minimal user."""
    from flask import request
    from Models.userModel import User, Role
    try:
        if request.method == "GET":
            limit = int(request.args.get("limit", 50))
            users = User.objects.order_by("-id").limit(limit)
            return jsonify({"success": True, "items": [_serialize_user(u) for u in users]})

        # POST create
        data = request.get_json() or {}
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip().lower()
        phone = data.get("phone")
        password = data.get("password") or "changeme123"
        role = (data.get("role") or "user").lower()
        role_enum = Role.ADMIN if role == "admin" else Role.USER

        if not (name and email and phone):
            return jsonify({"success": False, "message": "name, email, phone required"}), 400

        u = User(
            name=name,
            email=email,
            phone=int(phone),
            password=password,
            password_confirm=password,
            role=role_enum,
            photo="default.jpg"
        )
        u.save()
        return jsonify({"success": True, "user": _serialize_user(u)}), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


def admin_user_delete(user_id):
    from Models.userModel import User
    try:
        u = User.objects(id=user_id).first()
        if not u:
            return jsonify({"success": False, "message": "User not found"}), 404
        u.delete()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


def admin_items_api():
    from Models.lostItemModel import LostItem
    from flask import request
    try:
        if request.method == "GET":
            limit = int(request.args.get("limit", 50))
            items = LostItem.objects.order_by("-created_at").limit(limit)
            def s(it):
                return {
                    "id": _safe_obj_id(it),
                    "title": getattr(it, "title", ""),
                    "status": getattr(it, "status", ""),
                    "category": getattr(it, "category", ""),
                    "city": getattr(it, "city_town", ""),
                    "created_at": getattr(it, "created_at", None),
                    "is_active": getattr(it, "is_active", True),
                }
            return jsonify({"success": True, "items": [s(i) for i in items]})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


def admin_item_delete(item_id):
    from Models.lostItemModel import LostItem
    try:
        it = LostItem.objects(id=item_id).first()
        if not it:
            return jsonify({"success": False, "message": "Item not found"}), 404
        it.delete()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


def admin_testimonials_api():
    from Models.testimonialModel import Testimonial
    from flask import request
    try:
        if request.method == "GET":
            limit = int(request.args.get("limit", 50))
            qs = Testimonial.objects.order_by("-created_at").limit(limit)
            def s(t):
                return {
                    "id": _safe_obj_id(t),
                    "message": getattr(t, "message", ""),
                    "is_public": getattr(t, "is_public", True),
                    "user_name": getattr(getattr(t, "user", None), "name", ""),
                    "created_at": getattr(t, "created_at", None),
                }
            return jsonify({"success": True, "items": [s(t) for t in qs]})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


def admin_testimonial_delete(tid):
    from Models.testimonialModel import Testimonial
    try:
        t = Testimonial.objects(id=tid).first()
        if not t:
            return jsonify({"success": False, "message": "Testimonial not found"}), 404
        t.delete()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


def admin_send_email():
    from flask import request
    from Utils.email import send_reset_email
    try:
        data = request.get_json() or {}
        to_email = (data.get("to") or "").strip()
        subject = (data.get("subject") or "").strip()
        body = (data.get("body") or "").strip()

        # Reuse debug sender; for now, we send a simple text email via reset util if subject empty
        if not to_email:
            return jsonify({"success": False, "message": "'to' is required"}), 400

        # Minimal: if a subject/body provided, craft a custom email using SMTP; else use reset helper
        if subject or body:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            import os
            sender = os.getenv("EMAIL_SENDER", "noreply@lostfound.com")
            msg = MIMEMultipart()
            msg["From"] = sender
            msg["To"] = to_email
            msg["Subject"] = subject or "Admin message"
            msg.attach(MIMEText(body or "(empty)", "plain"))
            smtp_host = os.getenv("SMTP_HOST", "localhost")
            smtp_port = int(os.getenv("SMTP_PORT", 1025))
            with smtplib.SMTP(smtp_host, smtp_port) as smtp:
                smtp.sendmail(sender, to_email, msg.as_string())
        else:
            # Fallback: send reset style email with a dummy URL
            send_reset_email(to_email, "https://example.com/reset/token")
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
