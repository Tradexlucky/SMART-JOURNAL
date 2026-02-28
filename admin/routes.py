"""Admin dashboard routes."""
import logging
from flask import Blueprint, render_template, request, jsonify, session
from auth.utils import admin_required
from database import get_db

logger = logging.getLogger(__name__)
admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
@admin_required
def dashboard():
    db = get_db()
    users = db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    logs = db.execute("""
        SELECT l.*, u.username FROM login_logs l
        LEFT JOIN users u ON l.user_id = u.id
        ORDER BY l.login_at DESC LIMIT 50
    """).fetchall()
    db.close()
    return render_template("admin.html", users=users, logs=logs, user=session["user"])


@admin_bp.route("/user/<int:uid>/action", methods=["POST"])
@admin_required
def user_action(uid):
    action = request.json.get("action")
    db = get_db()
    if action == "approve":
        db.execute("UPDATE users SET status='approved' WHERE id=?", (uid,))
    elif action == "block":
        db.execute("UPDATE users SET status='blocked' WHERE id=?", (uid,))
    elif action == "make_admin":
        db.execute("UPDATE users SET role='admin', status='approved' WHERE id=?", (uid,))
    elif action == "revoke_admin":
        db.execute("UPDATE users SET role='user' WHERE id=?", (uid,))
    else:
        db.close()
        return jsonify({"error": "Unknown action"}), 400
    db.commit()
    db.close()
    logger.info(f"Admin action '{action}' on user {uid}")
    return jsonify({"success": True})
