"""Risk calculator routes."""
from flask import Blueprint, render_template, request, jsonify, session
from auth.utils import login_required

risk_bp = Blueprint("risk", __name__)


@risk_bp.route("/")
@login_required
def calculator():
    return render_template("risk.html", user=session["user"])


@risk_bp.route("/calculate", methods=["POST"])
@login_required
def calculate():
    data = request.json
    capital = float(data["capital"])
    risk_pct = float(data["risk_pct"])
    entry = float(data["entry"])
    stop_loss = float(data["stop_loss"])
    target = float(data.get("target", 0))
    risk_amount = capital * (risk_pct / 100)
    sl_points = abs(entry - stop_loss)
    position_size = int(risk_amount / sl_points) if sl_points > 0 else 0
    max_loss = round(position_size * sl_points, 2)
    rr = 0
    reward_amount = 0
    if target and sl_points > 0:
        reward_points = abs(target - entry)
        rr = round(reward_points / sl_points, 2)
        reward_amount = round(position_size * reward_points, 2)
    return jsonify({
        "position_size": position_size,
        "risk_amount": round(risk_amount, 2),
        "max_loss": max_loss,
        "rr_ratio": rr,
        "potential_profit": reward_amount,
        "sl_points": round(sl_points, 2),
        "capital_at_risk_pct": round((max_loss / capital) * 100, 2)
    })
