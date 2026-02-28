"""User profile routes — set Telegram Chat ID etc."""
from flask import Blueprint, render_template, request, jsonify, session
from auth.utils import login_required
from database import get_db

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile/telegram", methods=["POST"])
@login_required
def set_telegram():
    chat_id = request.json.get("chat_id", "").strip()
    user_id = session["user"]["id"]
    db = get_db()
    db.execute("UPDATE users SET telegram_chat_id=? WHERE id=?", (chat_id, user_id))
    db.commit()
    db.close()
    session["user"]["telegram_chat_id"] = chat_id
    return jsonify({"success": True})
