"""
TCF Discovery Agent — Flask App
Stage 1 of the AI Career Guidance System

Developed by Qarib Javed
"""

import os
from functools import wraps
from flask import Flask, render_template, request, jsonify, Response

from discovery_engine import (
    get_all_questions,
    parse_submission,
    run_discovery_assessment,
)
import database

app = Flask(__name__)
database.init_db()

# Change this before the pilot — this is what protects the counsellor dashboard.
# Better practice: set it as an environment variable instead of hardcoding.
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "tcf-counsellor-2026")


def require_dashboard_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.password != DASHBOARD_PASSWORD:
            return Response(
                "Authentication required.", 401,
                {"WWW-Authenticate": 'Basic realm="Counsellor Dashboard"'}
            )
        return f(*args, **kwargs)
    return wrapper


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/questions")
def api_questions():
    return jsonify(get_all_questions())


@app.route("/api/submit", methods=["POST"])
def api_submit():
    payload = request.get_json(force=True)
    try:
        student = parse_submission(payload)
        result = run_discovery_assessment(student)

        skills_ratings_serializable = {
            k: {"rating": v[0], "reason": v[1]} for k, v in student.skills_ratings.items()
        }
        submission_id = database.save_submission(
            student_name=student.student_name,
            skills_ratings=skills_ratings_serializable,
            result=result,
            academic_ratings=student.academic_ratings,
        )
        result["submission_id"] = submission_id
        result["skills_ratings"] = [
            [k, v[0], v[1]] for k, v in student.skills_ratings.items()
        ]
        result["academic_ratings"] = student.academic_ratings

        return jsonify({"ok": True, "result": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/dashboard")
@require_dashboard_auth
def dashboard():
    submissions = database.get_all_submissions()
    return render_template("dashboard.html", submissions=submissions)


@app.route("/dashboard/<int:submission_id>")
@require_dashboard_auth
def dashboard_detail(submission_id):
    submission = database.get_submission_by_id(submission_id)
    if submission is None:
        return "Submission not found.", 404
    return render_template("dashboard_detail.html", s=submission)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
