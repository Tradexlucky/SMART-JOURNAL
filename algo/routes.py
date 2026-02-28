"""Algo scanner routes."""
import logging
from flask import Blueprint, render_template, request, jsonify, session
from auth.utils import login_required, admin_required
from algo.models import get_latest_scan, save_scan_results
from database import get_db
import datetime

logger = logging.getLogger(__name__)
algo_bp = Blueprint("algo", __name__)


@algo_bp.route("/")
@login_required
def scanner():
    results = get_latest_scan()
    return render_template("scanner.html", results=results, user=session["user"])


@algo_bp.route("/results")
@login_required
def results_api():
    results = get_latest_scan()
    return jsonify(results)


@algo_bp.route("/add", methods=["POST"])
@admin_required
def add_stock():
    """Admin manually stock add karto."""
    data = request.json
    symbol    = data.get("symbol", "").upper().strip()
    signal    = data.get("signal", "BUY").upper()
    price     = float(data.get("price", 0))
    entry     = float(data.get("entry", 0))
    sl        = float(data.get("sl", 0))
    tp        = float(data.get("tp", 0))
    notes     = data.get("notes", "")

    if not symbol:
        return jsonify({"error": "Symbol required"}), 400

    # Conditions string banav
    conditions = f"Entry:₹{entry} SL:₹{sl} TP:₹{tp}"
    if notes:
        conditions += f" | {notes}"

    today = datetime.date.today().strftime("%Y-%m-%d")

    db = get_db()
    # Check if already exists
    existing = db.execute(
        "SELECT id FROM scan_results WHERE scan_date=? AND symbol=?",
        (today, symbol)
    ).fetchone()

    if existing:
        db.execute("""
            UPDATE scan_results
            SET signal=?, price=?, conditions_met=?, entry=?, sl=?, tp=?
            WHERE scan_date=? AND symbol=?
        """, (signal, price, conditions, entry, sl, tp, today, symbol))
    else:
        db.execute("""
            INSERT INTO scan_results
            (scan_date, symbol, signal, price, conditions_met, entry, sl, tp)
            VALUES (?,?,?,?,?,?,?,?)
        """, (today, symbol, signal, price, conditions, entry, sl, tp))

    db.commit()
    db.close()
    logger.info(f"Admin added stock: {symbol} {signal} Entry:{entry} SL:{sl} TP:{tp}")
    return jsonify({"success": True})


@algo_bp.route("/delete/<int:sid>", methods=["DELETE"])
@admin_required
def delete_stock(sid):
    """Admin stock delete karto."""
    db = get_db()
    db.execute("DELETE FROM scan_results WHERE id=?", (sid,))
    db.commit()
    db.close()
    return jsonify({"success": True})


@algo_bp.route("/run", methods=["POST"])
@admin_required
def run_scan():
    """Manual scan trigger."""
    from scheduler.tasks import run_algo_scan
    try:
        run_algo_scan()
        return jsonify({"success": True, "message": "Scan completed"})
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        return jsonify({"error": str(e)}), 500