"""Interest calculation and crediting service.

Interest accrues on ALL savings deposits (locked AND unlocked) until withdrawn.
Rate is weekly (e.g., 5% of $100 = $5/week). Interest is paid into the cash
account — not back into savings (no compounding).
"""

from datetime import datetime

from flask import current_app

from app.extensions import db
from app.models.bank import BankAccount, SavingsDeposit, Transaction


def _cfg_float(appconfig_key: str, flask_key: str, default: float) -> float:
    """Read a float config value from AppConfig DB, falling back to Flask config."""
    from app.models.security import AppConfig
    val = AppConfig.get(appconfig_key)
    if val is not None:
        try:
            return float(val)
        except (ValueError, TypeError):
            pass
    return float(current_app.config.get(flask_key, default))


def _get_active_savings_total(user_id: int) -> float:
    """Sum of all non-withdrawn savings deposits for a user."""
    deposits = SavingsDeposit.query.filter_by(
        user_id=user_id, withdrawn=False
    ).all()
    return sum(d.amount for d in deposits)


def calculate_interest(user_id: int) -> float:
    """Calculate interest owed since last credit.

    Returns the dollar amount of interest earned (not yet credited).
    Prorates the weekly rate based on seconds elapsed.
    """
    account = BankAccount.query.filter_by(user_id=user_id).first()
    if not account:
        return 0.0

    total_savings = _get_active_savings_total(user_id)
    if total_savings <= 0:
        return 0.0

    weekly_rate = _cfg_float("interest_rate", "INTEREST_RATE_WEEKLY", 0.05)
    weekly_interest = total_savings * weekly_rate

    if account.last_interest_credit:
        elapsed = (datetime.utcnow() - account.last_interest_credit).total_seconds()
    else:
        # First time — use account creation as baseline
        elapsed = (datetime.utcnow() - account.created_at).total_seconds()

    seconds_per_week = 7 * 24 * 60 * 60
    return weekly_interest * (elapsed / seconds_per_week)


def credit_interest(user_id: int) -> float:
    """Calculate and credit interest to cash_balance.

    Creates a Transaction record and updates the BankAccount.
    Returns the amount credited.
    """
    account = BankAccount.query.filter_by(user_id=user_id).first()
    if not account:
        return 0.0

    amount = calculate_interest(user_id)
    if amount <= 0:
        return 0.0

    # Round to 2 decimal places for the actual credit
    amount = round(amount, 2)
    if amount <= 0:
        return 0.0

    now = datetime.utcnow()
    account.cash_balance += amount
    account.total_interest_earned += amount
    account.last_interest_credit = now

    db.session.add(Transaction(
        user_id=user_id,
        type=Transaction.TYPE_INTEREST,
        amount=amount,
        balance_after=round(account.cash_balance, 2),
        description=f"Weekly interest on ${_get_active_savings_total(user_id):.2f} savings",
        created_at=now,
    ))
    db.session.commit()

    return amount


def get_ticker_data(user_id: int) -> dict:
    """Return data needed for the client-side interest ticker.

    The client uses this to calculate and display a continuously
    ticking interest amount via requestAnimationFrame.
    """
    account = BankAccount.query.filter_by(user_id=user_id).first()
    total_savings = _get_active_savings_total(user_id)
    weekly_rate = _cfg_float("interest_rate", "INTEREST_RATE_WEEKLY", 0.05)

    if not account:
        return {
            "total_active_savings": 0.0,
            "weekly_rate": weekly_rate,
            "last_interest_credit": None,
            "accrued_interest": 0.0,
        }

    last_credit = account.last_interest_credit or account.created_at

    # Cash balance + unlocked savings for nav ticker total-available calculation
    from app.models.bank import SavingsDeposit
    now = datetime.utcnow()
    unlocked_total = sum(
        d.amount for d in SavingsDeposit.query.filter(
            SavingsDeposit.user_id == user_id,
            SavingsDeposit.withdrawn == False,  # noqa: E712
            SavingsDeposit.lock_until <= now,
        ).all()
    )

    return {
        "total_active_savings": round(total_savings, 2),
        "weekly_rate": weekly_rate,
        "last_interest_credit": (last_credit.isoformat() + "Z") if last_credit else None,
        "accrued_interest": round(calculate_interest(user_id), 6),
        "cash_balance": round(account.cash_balance, 2),
        "unlocked_savings": round(unlocked_total, 2),
    }
