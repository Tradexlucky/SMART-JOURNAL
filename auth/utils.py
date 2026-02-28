"""Auth utility functions and decorators."""

import functools
from flask import session, redirect, url_for


def login_required(f):
    """Decorator to require login."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login"))
        if session["user"].get("status") not in ("approved",):
            return redirect(url_for("auth.pending"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator to require admin role."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login"))
        if session["user"].get("role") != "admin":
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated
