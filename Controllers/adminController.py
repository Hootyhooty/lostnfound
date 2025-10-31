import os
import gzip
import re
from datetime import datetime
from collections import defaultdict
from flask import render_template, flash, jsonify

LOG_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2}) .* \[(INFO|ERROR|WARNING)\]")

def parse_logs(days=7):
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
    """Optional route for async Chart.js or API access"""
    try:
        data = parse_logs(days=7)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
