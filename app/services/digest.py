"""Weekly family digest email service."""

from datetime import date

from flask import current_app

from app.extensions import db
from app.models.chore import ChoreHistory
from app.models.user import User
from app.services.allowance import calculate_allowance
from app.services.email import send_email
from app.services.xp import get_level_info


def send_weekly_digest() -> list[str]:
    """Send a family summary email to all admin users with email configured.

    Returns list of addresses sent to (empty if no admin emails or dry-run).
    Safe to call in dev/test — email.send_email() dry-runs when Mailgun keys missing.
    """
    today = date.today()
    week_str = today.strftime("%B %d, %Y")
    subject = f"Felker Family Hub — Week of {week_str}"

    # Build per-kid summary blocks
    kids = User.query.filter_by(is_admin=False).order_by(User.username).all()

    lines = [
        f"Felker Family Hub — Week of {week_str}",
        "=" * 44,
        "",
    ]

    for kid in kids:
        history = ChoreHistory.query.filter_by(
            username=kid.username, date=today
        ).all()

        total = len(history)
        done = sum(1 for h in history if h.completed)
        pct = round(done / total * 100) if total > 0 else 0

        allowance_earned = calculate_allowance(total, done, kid.allowance or 0)

        level_info = get_level_info(kid.id)

        account = kid.bank_account
        cash_balance = round(account.cash_balance, 2) if account else 0.0

        if account:
            from app.models.bank import SavingsDeposit
            active_deposits = SavingsDeposit.query.filter_by(
                user_id=kid.id, withdrawn=False
            ).all()
            total_savings = round(sum(d.amount for d in active_deposits), 2)
        else:
            total_savings = 0.0

        fire_status = "Yes" if kid.fire_mode else "No"

        lines += [
            f"--- {kid.username} ---",
            f"  Chores:          {done}/{total} ({pct}%)",
            f"  Allowance earned: ${allowance_earned:.2f}",
            f"  Level:           {level_info['level']} ({level_info['level_name']})",
            f"  Cash balance:    ${cash_balance:.2f}",
            f"  Savings total:   ${total_savings:.2f}",
            f"  Fire Mode:       {fire_status}",
            "",
        ]

    body = "\n".join(lines)

    # Send to all admin users with email configured
    admins = User.query.filter_by(is_admin=True).all()
    sent_to: list[str] = []

    for admin in admins:
        if admin.email:
            try:
                send_email(admin.email, subject, body)
                sent_to.append(admin.email)
            except Exception as exc:
                current_app.logger.error(
                    "Digest email failed for %s: %s", admin.email, exc
                )

    if not sent_to:
        current_app.logger.info(
            "DIGEST (dry-run — no admin emails configured)\n%s", body
        )

    return sent_to
