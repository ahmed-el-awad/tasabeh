from flask import Blueprint, request, jsonify
from models import db, Course, Session
from routes.auth_routes import require_admin_key

session_bp = Blueprint("sessions", __name__, url_prefix="/sessions")

@session_bp.route("/start", methods=["POST"])
def start_session():
    if not require_admin_key():
        return jsonify({"error":"unauthorized"}), 401
    data = request.get_json() or {}
    course_id = data.get("course_id")
    min_presence = data.get("min_presence_minutes", 30)
    heartbeat = data.get("heartbeat_minutes", 10)
    grace = data.get("grace_minutes", 5)

    s = Session(course_id=course_id, min_presence_minutes=min_presence,
                heartbeat_minutes=heartbeat, grace_minutes=grace)
    db.session.add(s)
    db.session.commit()
    return jsonify({"message":"session_started","session_id": s.id})

@session_bp.route("/end", methods=["POST"])
def end_session():
    if not require_admin_key():
        return jsonify({"error":"unauthorized"}), 401
    data = request.get_json() or {}
    session_id = data.get("session_id")
    s = Session.query.get(session_id)
    if not s:
        return jsonify({"error":"not_found"}), 404
    from datetime import datetime
    s.end_time = datetime.utcnow()
    db.session.commit()
    return jsonify({"message":"session_ended","session_id": s.id})
