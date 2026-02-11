"""Application configuration.

Defaults are defined here. Runtime-editable values are stored in the
AppConfig DB table and override these defaults via the admin UI.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'chores.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security defaults (overridable via AppConfig table)
    PIN_HASH = os.getenv("PIN_HASH", "")  # bcrypt hash of 4-digit PIN
    IDLE_TIMEOUT_MINUTES = 5
    TRUSTED_IP_EXPIRY_DAYS = 7
    PIN_MAX_ATTEMPTS = 5
    PIN_LOCKOUT_MINUTES = 15

    # Bank defaults
    INTEREST_RATE_WEEKLY = 0.05
    SAVINGS_MAX = 100.00
    SAVINGS_LOCK_DAYS = 30
    CASHOUT_MIN = 1.00
    SAVINGS_DEPOSIT_MIN = 1.00

    # Mailgun
    MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY", "")
    MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN", "")
    MAILGUN_BASE_URL = os.getenv("MAILGUN_BASE_URL", "https://api.mailgun.net")

    # Google Calendar
    GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "")

    # Scheduler
    SCHEDULER_API_ENABLED = True


class TestConfig(Config):
    """Testing configuration — in-memory DB, no external services."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    PIN_HASH = ""  # Disable PIN in tests by default
    MAILGUN_API_KEY = ""
    GOOGLE_SERVICE_ACCOUNT_JSON = ""
