"""Trading journal routes."""
import os
import logging
from flask import Blueprint, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
from auth.utils import login_required
from journal.models import get_all_trades, get_analytics
from database import get_db

logger = logging.getLogger(__name__)
journal_bp = Blueprint("journal", __name__)
ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


@journal_bp.route("/")
@login_required
def journal():
    user = session["user"]
    symbol = request.args.get("symbol", "")
    date_from = request.args.get("from", "")
    date_to = request.args.get("to", "")
    trades = get_all_trades(user["id"], symbol, date_from or None, date_to or None)
    analytics = get_analytics(user["id"])
    return render_template("journal.html", trades=trades, analytics=analytics,
                           user=user, symbol=symbol, date_from=date_from, date_to=date_to)


@journal_bp.route("/add", methods=["POST"])
@login_required
def add_trade():
    user = session["user"]
    data = request.form
    entry = float(data["entry_price"])
    sl = float(data["stop_loss"])
    target = float(data["target_price"])
    exit_price = float(data["exit_price"]) if data.get("exit_price") else None
    risk = abs(entry - sl)
    reward = abs(target - entry)
    rr = round(reward / risk, 2) if risk > 0 else 0
    result = None
    pnl = None
    r_multiple = None
    qty = int(data.get("quantity", 1))
    if exit_price:
        if data.get("direction", "LONG") == "LONG":
            pnl = round((exit_price - entry) * qty, 2)
        else:
            pnl = round((entry - exit_price) * qty, 2)
        result = "WIN" if pnl > 0 else "LOSS"
        r_multiple = round(pnl / (risk * qty), 2) if risk > 0 else 0
    screenshot_path = None
    if "screenshot" in request.files:
        file = request.files["screenshot"]
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{user['id']}_{file.filename}")
            upload_dir = os.path.join("static", "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))
            screenshot_path = f"uploads/{filename}"
    db = get_db()
    db.execute("""
        INSERT INTO trades (user_id, trade_date, symbol, direction, entry_price, stop_loss,
            target_price, exit_price, quantity, result, pnl, r_multiple, notes, screenshot_path)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (user["id"], data["trade_date"], data["symbol"].upper(), data.get("direction", "LONG"),
          entry, sl, target, exit_price, qty, result, pnl, r_multiple, data.get("notes", ""), screenshot_path))
    db.commit()
    db.close()
    return jsonify({"success": True})


@journal_bp.route("/delete/<int:tid>", methods=["DELETE"])
@login_required
def delete_trade(tid):
    user = session["user"]
    db = get_db()
    db.execute("DELETE FROM trades WHERE id=? AND user_id=?", (tid, user["id"]))
    db.commit()
    db.close()
    return jsonify({"success": True})
