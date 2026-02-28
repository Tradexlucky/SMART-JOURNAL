"""Email and Telegram notification utilities."""

import os
import logging
import smtplib
import urllib.request
import urllib.parse
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import get_db

logger = logging.getLogger(__name__)


def send_telegram(chat_id: str, message: str):
    """Send a Telegram message via Bot API."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or not chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "HTML"}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


def send_email(to_email: str, subject: str, body: str):
    """Send email via SMTP."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    from_email = os.getenv("FROM_EMAIL", smtp_user)

    if not smtp_user or not smtp_pass:
        logger.warning("SMTP not configured — skipping email")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Email send failed to {to_email}: {e}")
        return False


def send_scan_notification(results: list, scan_date: str):
    """Broadcast scan results to all approved users."""
    db = get_db()
    users = db.execute(
        "SELECT * FROM users WHERE status='approved'"
    ).fetchall()
    db.close()

    symbols = ", ".join(r["symbol"] for r in results[:10])
    count = len(results)
    text_msg = (
        f"📊 <b>SwingTrader Pro — Daily Scan ({scan_date})</b>\n\n"
        f"✅ {count} signals found\n\n"
        f"<b>Stocks:</b> {symbols}\n\n"
        f"Login to view full details."
    )
    email_body = f"""
    <h2>SwingTrader Pro — Daily Scan Results</h2>
    <p><b>Date:</b> {scan_date}</p>
    <p><b>{count} signals found</b></p>
    <table border='1' cellpadding='8' style='border-collapse:collapse'>
      <tr><th>Symbol</th><th>Signal</th><th>Price</th><th>Conditions</th></tr>
      {''.join(f"<tr><td>{r['symbol']}</td><td>{r['signal']}</td><td>₹{r['price']}</td><td>{r.get('conditions_met','')}</td></tr>" for r in results)}
    </table>
    """

    for user in users:
        if user["telegram_chat_id"]:
            send_telegram(user["telegram_chat_id"], text_msg)
        if user["email"]:
            send_email(user["email"], f"📊 {count} Swing Signals — {scan_date}", email_body)

    logger.info(f"Notifications sent to {len(users)} users")
