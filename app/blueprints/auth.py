"""Authentication blueprint — PIN verification, IP trust, session management."""

import math
from datetime import datetime, timedelta

import bcrypt
from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.extensions import db
from app.models.security import AppConfig, PinAttempt, TrustedIP
from app.models.user import User

auth_bp = Blueprint("auth", __name__)

# How long a trusted IP lasts before requiring re-auth
TRUST_EXPIRY_DAYS = 7
# Rate-limiting
MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def _utcnow():
    """Naive UTC datetime — consistent with SQLite storage."""
    return datetime.utcnow()


# ── helpers ──────────────────────────────────────────────────────────

def _client_ip():
    """Get the client IP, respecting X-Forwarded-For behind a reverse proxy."""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "127.0.0.1"


def _is_ip_trusted(ip):
    """Check whether the IP is in the TrustedIP table and not expired."""
    cutoff = _utcnow() - timedelta(days=TRUST_EXPIRY_DAYS)
    row = TrustedIP.query.filter_by(ip_address=ip).first()
    if row and row.trusted_at >= cutoff:
        row.last_seen = _utcnow()
        db.session.commit()
        return True
    return False


def _trust_ip(ip):
    """Add or refresh a TrustedIP entry."""
    now = _utcnow()
    row = TrustedIP.query.filter_by(ip_address=ip).first()
    if row:
        row.trusted_at = now
        row.last_seen = now
    else:
        row = TrustedIP(ip_address=ip, trusted_at=now, last_seen=now)
        db.session.add(row)
    db.session.commit()


def _check_lockout(ip):
    """Return minutes remaining on lockout, or 0 if not locked out."""
    cutoff = _utcnow() - timedelta(minutes=LOCKOUT_MINUTES)
    recent_failures = PinAttempt.query.filter(
        PinAttempt.ip_address == ip,
        PinAttempt.attempted_at >= cutoff,
        PinAttempt.success == False,  # noqa: E712
    ).count()
    if recent_failures >= MAX_ATTEMPTS:
        oldest_in_window = (
            PinAttempt.query.filter(
                PinAttempt.ip_address == ip,
                PinAttempt.attempted_at >= cutoff,
                PinAttempt.success == False,  # noqa: E712
            )
            .order_by(PinAttempt.attempted_at.asc())
            .first()
        )
        if oldest_in_window:
            unlock_at = oldest_in_window.attempted_at + timedelta(
                minutes=LOCKOUT_MINUTES
            )
            remaining = (unlock_at - _utcnow()).total_seconds()
            return max(1, math.ceil(remaining / 60))
    return 0


def _record_attempt(ip, success):
    db.session.add(
        PinAttempt(
            ip_address=ip,
            attempted_at=_utcnow(),
            success=success,
        )
    )
    db.session.commit()


def _verify_pin(pin_input):
    """Verify a PIN against the stored bcrypt hash in AppConfig."""
    stored_hash = AppConfig.get("pin_hash", "")
    if not stored_hash:
        # No PIN configured — let everyone in
        return True
    try:
        return bcrypt.checkpw(
            pin_input.encode("utf-8"), stored_hash.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


# ── before-request hook (registered on app) ─────────────────────────

def require_trusted_ip():
    """Before-request hook: redirect untrusted IPs to /pin."""
    # Exempt paths
    if request.path.startswith("/static"):
        return None
    if request.path in ("/pin", "/favicon.ico"):
        return None
    if request.method == "POST" and request.path == "/pin":
        return None

    # If no PIN is configured, skip auth entirely
    pin_hash = AppConfig.get("pin_hash", "")
    if not pin_hash:
        return None

    ip = _client_ip()
    if _is_ip_trusted(ip):
        return None

    return redirect(url_for("auth.pin_page"))


# ── routes ───────────────────────────────────────────────────────────

@auth_bp.route("/pin", methods=["GET"])
def pin_page():
    ip = _client_ip()
    lockout = _check_lockout(ip)
    return render_template("pin.html", lockout_remaining=lockout, error=None)


@auth_bp.route("/pin", methods=["POST"])
def pin_submit():
    ip = _client_ip()
    lockout = _check_lockout(ip)
    if lockout:
        return render_template(
            "pin.html",
            lockout_remaining=lockout,
            error=None,
        )

    pin_input = request.form.get("pin", "")

    if _verify_pin(pin_input):
        _record_attempt(ip, success=True)
        _trust_ip(ip)
        return redirect(url_for("auth.login_page"))
    else:
        _record_attempt(ip, success=False)
        lockout = _check_lockout(ip)
        error = "Incorrect PIN" if not lockout else None
        return render_template(
            "pin.html",
            lockout_remaining=lockout,
            error=error,
        )


# ── session routes ───────────────────────────────────────────────────

@auth_bp.route("/", methods=["GET"])
def login_page():
    """User selection screen."""
    if session.get("current_user_id"):
        return redirect(url_for("chores.home"))
    users = User.query.order_by(User.id).all()
    return render_template("login.html", users=users)


@auth_bp.route("/session", methods=["POST"])
def create_session():
    """Set the current user in the session."""
    user_id = request.form.get("user_id", type=int)
    if not user_id:
        return redirect(url_for("auth.login_page"))
    user = db.session.get(User, user_id)
    if not user:
        return redirect(url_for("auth.login_page"))
    session["current_user_id"] = user.id
    return redirect(url_for("chores.home"))


@auth_bp.route("/session/logout")
def logout():
    """Clear the session and go back to login."""
    session.pop("current_user_id", None)
    return redirect(url_for("auth.login_page"))
