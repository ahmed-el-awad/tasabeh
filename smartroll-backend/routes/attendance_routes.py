from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db, Student, Session, AttendanceLog, ApprovedSubnet
from sqlalchemy import desc
from routes.auth_routes import require_admin_key

attendance_bp = Blueprint("attendance_bp", __name__, url_prefix="/attendance")

# -------------------------
# Helper — Check if IP is allowed
# -------------------------
def ip_in_approved_subnet(client_ip: str) -> bool:
    if not client_ip:
        return False

    subnets = ApprovedSubnet.query.all()
    for subnet in subnets:
        prefix = subnet.prefix.strip()
        if client_ip.startswith(prefix):
            return True

    return False


# =====================================================
# 1) STUDENT SELF CHECK-IN
# =====================================================
@attendance_bp.post("/check_in")
def check_in():
    data = request.get_json() or {}

    mac = (data.get("mac") or "").upper()
    session_id = data.get("session_id")

    print("DEBUG-1: Incoming MAC =", mac)
    print("DEBUG-2: Incoming session_id =", session_id)

    if not mac or not session_id:
        return jsonify({"error": "missing_fields"}), 400

    # Receive real device IP from Flutter
    client_ip = data.get("device_ip") or request.remote_addr
    print("DEBUG-3: Client IP =", client_ip)

    # Subnet validation
    if not ip_in_approved_subnet(client_ip):
        print("DEBUG-4: Subnet FAILED")
        return jsonify({"error": "You must be on classroom Wi-Fi"}), 403

    print("DEBUG-4: Subnet OK")

    # Validate student
    student = Student.query.filter_by(mac_address=mac).first()
    print("DEBUG-5: Student =", student)

    if not student:
        return jsonify({"error": "unknown_device"}), 404

    # Validate session
    s = Session.query.get(session_id)
    print("DEBUG-6: Session =", s)

    if not s:
        return jsonify({"error": "session_not_found"}), 404

    # Create log entry
    log = AttendanceLog(
        session_id=session_id,
        student_id=student.id,
        mac=mac,
        status="Heartbeat",
        timestamp=datetime.utcnow()
    )

    print("DEBUG-7: Log created:", log)

    # Commit safely
    try:
        db.session.add(log)
        db.session.commit()
        print("DEBUG-8: Commit OK")
    except Exception as e:
        print("DEBUG-8: Commit FAILED:", e)
        return jsonify({"error": "db_commit_failed"}), 500

    print("DEBUG-9: Total logs now =", AttendanceLog.query.count())

    return jsonify({
        "message": "check_in_recorded",
        "student": student.name
    }), 200


# =====================================================
# 2) ROUTER PUSH ENDPOINT (ADMIN ONLY)
# =====================================================
@attendance_bp.post("/router_push")
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

    for dev in devices:
        mac = (dev.get("mac") or "").upper()
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


# =====================================================
# 3) INSTRUCTOR VIEW LOGS (Newest → Oldest)
# =====================================================
@attendance_bp.get("/session/<int:session_id>")
def session_logs(session_id):
    logs = AttendanceLog.query.filter_by(
        session_id=session_id
    ).order_by(desc(AttendanceLog.timestamp)).all()

    out = [{
        "student_id": l.student_id,
        "mac": l.mac,
        "status": l.status,
        "timestamp": l.timestamp.isoformat()
    } for l in logs]

    return jsonify(out), 200
