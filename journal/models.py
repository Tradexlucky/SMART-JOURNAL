"""Trading journal data models."""
from database import get_db


def get_recent_trades(user_id: int, limit: int = 10):
    db = get_db()
    rows = db.execute("""
        SELECT * FROM trades WHERE user_id=?
        ORDER BY trade_date DESC, created_at DESC LIMIT ?
    """, (user_id, limit)).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_all_trades(user_id, symbol=None, date_from=None, date_to=None):
    db = get_db()
    query = "SELECT * FROM trades WHERE user_id=?"
    params = [user_id]
    if symbol:
        query += " AND symbol LIKE ?"
        params.append(f"%{symbol.upper()}%")
    if date_from:
        query += " AND trade_date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND trade_date <= ?"
        params.append(date_to)
    query += " ORDER BY trade_date DESC, created_at DESC"
    rows = db.execute(query, params).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_analytics(user_id: int):
    db = get_db()
    trades = db.execute(
        "SELECT * FROM trades WHERE user_id=? AND result IS NOT NULL", (user_id,)
    ).fetchall()
    db.close()

    total = len(trades)
    if total == 0:
        return {
            "total": 0, "wins": 0, "losses": 0,
            "win_rate": 0, "avg_rr": 0, "total_pnl": 0
        }

    wins   = sum(1 for t in trades if t["result"] == "WIN")
    losses = sum(1 for t in trades if t["result"] == "LOSS")
    total_pnl = sum(t["pnl"] or 0 for t in trades)
    rr_vals = [t["r_multiple"] for t in trades if t["r_multiple"] is not None]
    avg_rr = sum(rr_vals) / len(rr_vals) if rr_vals else 0

    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "win_rate": round((wins / total) * 100, 1),
        "avg_rr": round(avg_rr, 2),
        "total_pnl": round(total_pnl, 2)
    }

