# 📈 SwingTrader Pro

Professional swing trading platform for the Indian stock market.

## Features

- 🔐 **GitHub OAuth** — secure login, role-based access (Admin / User)
- 🤖 **Algo Scanner** — plug-in `algo/algo.py` with your strategy; auto-runs at 4:30 PM IST
- 📰 **Market News** — live Indian market news from ET & Moneycontrol RSS
- ⚡ **Risk Calculator** — position sizing, R:R, max loss calculator
- 📖 **Trading Journal** — full trade tracking with P&L, R-multiples, analytics
- 👑 **Admin Panel** — approve/block users, view login logs
- 📬 **Notifications** — Telegram Bot + Email scan alerts

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 3. Run
python app.py
```

Open http://localhost:5000

## Directory Structure

```
swingtrader/
├── app.py              ← Flask entry point
├── database.py         ← SQLite init & connection
├── auth/               ← GitHub OAuth routes & utils
├── admin/              ← Admin panel (user mgmt, logs)
├── algo/
│   ├── algo.py         ← ⭐ YOUR TRADING ALGORITHM HERE
│   ├── models.py
│   └── routes.py
├── journal/            ← Trade logging & analytics
├── news/               ← RSS news fetcher
├── risk/               ← Position size calculator
├── scheduler/          ← APScheduler + notifications
├── static/css/         ← Dark theme CSS
├── static/js/          ← Vanilla JS
└── templates/          ← Jinja2 HTML templates
```

## Customizing the Algo

Edit `algo/algo.py` — the `scan()` function is called daily:
```python
def scan() -> list:
    # Return: [{"symbol": "RELIANCE", "signal": "BUY", "price": 2500.0, "conditions_met": "EMA Cross | RSI 58"}]
```

Integrate any data source: `yfinance`, Zerodha Kite API, NSE India API, etc.

## Setting Telegram Chat ID

Users can set their Telegram Chat ID from the profile. To get your ID:
1. Start a chat with your bot on Telegram
2. Visit: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Find `chat.id` in the response

## GitHub OAuth Setup

1. Go to https://github.com/settings/developers → New OAuth App
2. Set Homepage URL: `http://localhost:5000`
3. Set Callback URL: `http://localhost:5000/auth/callback`
4. Copy Client ID & Secret to `.env`

## Environment Variables

See `.env.example` for all configuration options.

## Production Deployment

```bash
# Use gunicorn
pip install gunicorn
gunicorn app:create_app() --bind 0.0.0.0:5000 --workers 2
```

Set `DEBUG=false` and use a strong `SECRET_KEY` in production.
