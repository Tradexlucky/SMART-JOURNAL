"""
SwingTrader Pro - Main Application Entry Point
Indian Stock Market Swing Trading Platform
"""

import logging
import os
from flask import Flask
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("swingtrader.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")
    app.config["UPLOAD_FOLDER"] = "static/uploads"
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB max upload

    # Initialize database
    from database import init_db
    init_db()

    # Register blueprints
    from auth.routes import auth_bp
    from admin.routes import admin_bp
    from algo.routes import algo_bp
    from journal.routes import journal_bp
    from risk.routes import risk_bp
    from news.routes import news_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(algo_bp, url_prefix="/algo")
    app.register_blueprint(journal_bp, url_prefix="/journal")
    app.register_blueprint(risk_bp, url_prefix="/risk")
    app.register_blueprint(news_bp, url_prefix="/news")

    # Main routes
    from flask import render_template, session, redirect, url_for
    from auth.utils import login_required

    @app.route("/")
    def index():
        if "user" not in session:
            return redirect(url_for("auth.login"))
        return redirect(url_for("dashboard"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        from journal.models import get_recent_trades
        from algo.models import get_latest_scan
        from news.fetcher import get_cached_news

        user = session["user"]
        recent_trades = get_recent_trades(user["id"], limit=5)
        scan_results = get_latest_scan()
        news = get_cached_news(limit=6)

        from datetime import datetime
        return render_template(
            "dashboard.html",
             user=user,
             recent_trades=recent_trades,
             scan_results=scan_results,
                news=news,
             now=datetime.now()
        )

    # Initialize scheduler
    from scheduler.tasks import init_scheduler
    init_scheduler(app)

    logger.info("SwingTrader Pro initialized successfully")
    return app


if __name__ == "__main__":
    app = create_app()
    import os
    port = int(os.environ.get("PORT", 5000))
    pp.run(debug=False, host='0.0.0.0', port=port)
