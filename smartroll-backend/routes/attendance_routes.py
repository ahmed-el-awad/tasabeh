from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db, Student, Session, AttendanceLog, ApprovedSubnet
from utils.ip_utils import get_ip_prefix
from routes.auth_routes import require_admin_key

attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")

# 1) Student/app check-in (must be on approved classroom Wi-Fi)
@attendance_bp.route("/check_in", methods=["POST"])
def check_in():
    data = request.get_json() or {}
    mac = (data.get("mac") or "").upper()
    session_id = data.get("session_id")

    # Step 1: Get student's current network prefix
    client_prefix = get_ip_prefix()

    # Step 2: Verify that prefix matches an approved classroom
    allowed_prefix = ApprovedSubnet.query.filter(
        ApprovedSubnet.prefix.like(f"{client_prefix}%")
    ).first()

    if not allowed_prefix:
        return jsonify({"error": "You must be on classroom Wi-Fi"}), 403

    # Step 3: Validate student and session
    student = Student.query.filter_by(mac_address=mac).first()
    if not student:
        return jsonify({"error": "unknown_device"}), 404

    s = Session.query.get(session_id)
    if not s:
        return jsonify({"error": "session_not_found"}), 404

    # Step 4: Record the check-in log
    log = AttendanceLog(
        session_id=session_id,
        student_id=student.id,
        mac=mac,
        status="Heartbeat",
        timestamp=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "message": "check_in_recorded",
        "student": student.name,
        "classroom_prefix": allowed_prefix.prefix
    }), 200


# 2) Router/PI push (optional future: auto-detection)
@attendance_bp.route("/router_push", methods=["POST"])
def router_push():
    if not require_admin_key():
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json() or {}
    session_id = data.get("session_id")
    devices = data.get("connected_devices", [])

    s = Session.query.get(session_id)
    if not s:
        return jsonify({"error": "session_not_found"}), 404

    saved = 0
    for d in devices:
        mac = (d.get("mac") or "").upper()
        student = Student.query.filter_by(mac_address=mac).first()
        if not student:
            continue
        log = AttendanceLog(
            session_id=session_id,
            student_id=student.id,
            mac=mac,
            status="Heartbeat",
            timestamp=datetime.utcnow()
        )
        db.session.add(log)
        saved += 1
    db.session.commit()

    return jsonify({
        "message": "router_data_ingested",
        "count": saved
    }), 200


# 3) Instructor view of session logs
@attendance_bp.route("/session/<int:session_id>", methods=["GET"])
def session_logs(session_id):
    logs = AttendanceLog.query.filter_by(session_id=session_id).order_by(AttendanceLog.timestamp).all()
    out = [{
        "student_id": l.student_id,
        "mac": l.mac,
        "status": l.status,
        "timestamp": l.timestamp.isoformat()
    } for l in logs]
    return jsonify(out),404
