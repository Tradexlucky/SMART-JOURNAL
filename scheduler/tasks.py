"""
Scheduler — APScheduler based task runner.
Daily algo scan at 4:30 PM IST, news refresh every 30 min.
"""

import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


def run_algo_scan():
    """Run the algo scan and send notifications."""
    from algo.algo import scan
    from algo.models import save_scan_results
    from scheduler.notifications import send_scan_notification

    logger.info("Starting scheduled algo scan")
    today = datetime.now().strftime("%Y-%m-%d")
    results = scan()
    save_scan_results(results, today)

    if results:
        send_scan_notification(results, today)
    logger.info(f"Scan complete: {len(results)} signals saved")


def refresh_news():
    """Refresh news cache."""
    from news.fetcher import fetch_news
    try:
        fetch_news()
    except Exception as e:
        logger.error(f"News refresh failed: {e}")


def init_scheduler(app):
    """Initialize APScheduler with Flask app context."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        import pytz

        ist = pytz.timezone("Asia/Kolkata")
        scheduler = BackgroundScheduler(timezone=ist)

        # Daily scan at 4:30 PM IST (Mon-Fri)
        scheduler.add_job(
            lambda: app.app_context().__enter__() or run_algo_scan(),
            CronTrigger(day_of_week="mon-fri", hour=16, minute=30, timezone=ist),
            id="daily_scan",
            replace_existing=True
        )

        # News refresh every 30 minutes
        scheduler.add_job(
            lambda: app.app_context().__enter__() or refresh_news(),
            "interval",
            minutes=30,
            id="news_refresh",
            replace_existing=True
        )

        scheduler.start()
        logger.info("Scheduler started: scan at 4:30 PM IST, news every 30 min")

    except ImportError:
        logger.warning("APScheduler not installed — scheduler disabled. Run: pip install apscheduler pytz")
    except Exception as e:
        logger.error(f"Scheduler init failed: {e}")
