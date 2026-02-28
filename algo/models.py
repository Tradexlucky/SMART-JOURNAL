"""Algo scan result models."""

from database import get_db


def get_latest_scan():
    """Get today's or most recent scan results."""
    db = get_db()
    results = db.execute("""
        SELECT * FROM scan_results
        WHERE scan_date = (SELECT MAX(scan_date) FROM scan_results)
        ORDER BY scanned_at DESC
    """).fetchall()
    db.close()
    return [dict(r) for r in results]


def save_scan_results(results: list, scan_date: str):
    """Save scan results to DB."""
    db = get_db()
    db.execute("DELETE FROM scan_results WHERE scan_date = ?", (scan_date,))
    for r in results:
        db.execute("""
            INSERT INTO scan_results (scan_date, symbol, signal, price, conditions_met)
            VALUES (?,?,?,?,?)
        """, (scan_date, r["symbol"], r["signal"], r["price"], r.get("conditions_met", "")))
    db.commit()
    db.close()
