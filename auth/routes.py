"""
GitHub OAuth Authentication Routes
"""

import os
import logging
import requests
from flask import Blueprint, redirect, request, session, url_for, render_template
from database import get_db

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)


def get_github_config():
    """Get GitHub config fresh from env each time — fixes load order issue."""
    return {
        "client_id": os.getenv("GITHUB_CLIENT_ID", ""),
        "client_secret": os.getenv("GITHUB_CLIENT_SECRET", ""),
        "redirect_uri": os.getenv("GITHUB_REDIRECT_URI", "http://localhost:5000/auth/callback"),
    }


@auth_bp.route("/login")
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@auth_bp.route("/github")
def github_login():
    """Redirect to GitHub OAuth."""
    cfg = get_github_config()
    if not cfg["client_id"]:
        return "ERROR: GITHUB_CLIENT_ID not set in .env file!", 500

    scope = "read:user user:email"
    github_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={cfg['client_id']}"
        f"&redirect_uri={cfg['redirect_uri']}"
        f"&scope={scope}"
    )
    logger.info(f"Redirecting to GitHub OAuth: client_id={cfg['client_id'][:8]}...")
    return redirect(github_url)


@auth_bp.route("/callback")
def callback():
    """Handle GitHub OAuth callback."""
    cfg = get_github_config()
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        logger.error(f"GitHub OAuth error: {error}")
        return redirect(url_for("auth.login"))

    if not code:
        logger.error("No code in callback")
        return redirect(url_for("auth.login"))

    # Exchange code for token
    try:
        token_resp = requests.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
                "code": code,
            },
            headers={"Accept": "application/json"},
            timeout=15
        )
        token_data = token_resp.json()
    except Exception as e:
        logger.error(f"Token exchange failed: {e}")
        return f"Login failed: {e}", 500

    access_token = token_data.get("access_token")
    if not access_token:
        logger.error(f"No access token: {token_data}")
        return f"GitHub login failed: {token_data.get('error_description', 'No token received')}", 500

    # Fetch user info from GitHub
    try:
        user_resp = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15
        )
        gh_user = user_resp.json()

        email_resp = requests.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15
        )
        emails = email_resp.json()
        primary_email = next((e["email"] for e in emails if e.get("primary")), None)
    except Exception as e:
        logger.error(f"GitHub API call failed: {e}")
        return f"Failed to fetch GitHub user info: {e}", 500

    # Upsert user in DB
    db = get_db()
    existing = db.execute(
        "SELECT * FROM users WHERE github_id = ?", (str(gh_user["id"]),)
    ).fetchone()

    if existing:
        db.execute(
            "UPDATE users SET username=?, email=?, avatar_url=? WHERE github_id=?",
            (gh_user["login"], primary_email, gh_user.get("avatar_url"), str(gh_user["id"]))
        )
        user = dict(db.execute(
            "SELECT * FROM users WHERE github_id=?", (str(gh_user["id"]),)
        ).fetchone())
    else:
        is_admin = str(gh_user["id"]) == os.getenv("ADMIN_GITHUB_ID", "")
        role = "admin" if is_admin else "user"
        status = "approved" if is_admin else "pending"

        db.execute(
            "INSERT INTO users (github_id, username, email, avatar_url, role, status) VALUES (?,?,?,?,?,?)",
            (str(gh_user["id"]), gh_user["login"], primary_email, gh_user.get("avatar_url"), role, status)
        )
        user = dict(db.execute(
            "SELECT * FROM users WHERE github_id=?", (str(gh_user["id"]),)
        ).fetchone())

    # Log login
    db.execute(
        "INSERT INTO login_logs (user_id, ip_address, user_agent) VALUES (?,?,?)",
        (user["id"], request.remote_addr, request.user_agent.string[:255])
    )
    db.commit()
    db.close()

    session["user"] = {k: user[k] for k in user.keys()}
    logger.info(f"User {user['username']} logged in successfully as {user['role']}")

    if user["status"] == "pending":
        return redirect(url_for("auth.pending"))
    elif user["status"] == "blocked":
        return redirect(url_for("auth.blocked"))

    return redirect(url_for("dashboard"))


@auth_bp.route("/pending")
def pending():
    return render_template("pending.html", user=session.get("user"))


@auth_bp.route("/blocked")
def blocked():
    return render_template("blocked.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
