"""News dashboard routes."""

from flask import Blueprint, render_template, jsonify, session
from auth.utils import login_required
from news.fetcher import get_cached_news, fetch_news

news_bp = Blueprint("news", __name__)


@news_bp.route("/")
@login_required
def dashboard():
    news = get_cached_news(limit=30)
    return render_template("news.html", news=news, user=session["user"])


@news_bp.route("/refresh")
@login_required
def refresh():
    try:
        articles = fetch_news()
        return jsonify({"success": True, "count": len(articles)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@news_bp.route("/api")
@login_required
def api():
    news = get_cached_news(limit=20)
    return jsonify(news)
