"""
TCF Discovery Agent — Flask App
Stage 1 of the AI Career Guidance System

Developed by Qarib Javed
"""

import os
from flask import Flask, render_template, request, jsonify

from discovery_engine import (
    get_all_questions,
    parse_submission,
    run_discovery_assessment,
)

app = Flask(__name__)


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
        return jsonify({"ok": True, "result": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
