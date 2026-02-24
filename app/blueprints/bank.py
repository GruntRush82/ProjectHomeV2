"""Bank & savings routes — cashout, deposits, withdrawals, goals, ticker."""

from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, render_template, request, session

from app.extensions import db
from app.models.bank import BankAccount, SavingsDeposit, SavingsGoal, Transaction
from app.models.user import User
from app.services.interest import credit_interest, get_ticker_data, _cfg_float

bank_bp = Blueprint("bank", __name__)


def _bank_cfg(key: str) -> float:
    """Read a bank config float from AppConfig (admin-editable) with Flask config fallback."""
    _map = {
        "interest_rate":       ("INTEREST_RATE_WEEKLY", 0.05),
        "savings_max":         ("SAVINGS_MAX",          100.0),
        "savings_lock_days":   ("SAVINGS_LOCK_DAYS",    30.0),
        "cashout_min":         ("CASHOUT_MIN",           1.0),
        "savings_deposit_min": ("SAVINGS_DEPOSIT_MIN",   1.0),
    }
    flask_key, default = _map[key]
    return _cfg_float(key, flask_key, default)


# ── helpers ──────────────────────────────────────────────────────────

def _get_or_create_account(user_id):
    """Return the user's BankAccount, creating one if it doesn't exist."""
    account = BankAccount.query.filter_by(user_id=user_id).first()
    if not account:
        account = BankAccount(user_id=user_id)
        db.session.add(account)
        db.session.commit()
    return account


def _require_login():
    """Return (user_id, user) or (error_response, None)."""
    user_id = session.get("current_user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), None
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), None
    return user_id, user


def _active_deposits(user_id):
    """Return all non-withdrawn savings deposits for a user."""
    return SavingsDeposit.query.filter_by(
        user_id=user_id, withdrawn=False
    ).order_by(SavingsDeposit.deposited_at.asc()).all()


def _unlocked_deposits(user_id):
    """Return non-withdrawn, unlocked savings deposits."""
    now = datetime.utcnow()
    return SavingsDeposit.query.filter(
        SavingsDeposit.user_id == user_id,
        SavingsDeposit.withdrawn == False,  # noqa: E712
        SavingsDeposit.lock_until <= now,
    ).order_by(SavingsDeposit.deposited_at.asc()).all()


def _record_transaction(user_id, txn_type, amount, balance_after, description=""):
    """Create and add a Transaction to the session (does not commit)."""
    txn = Transaction(
        user_id=user_id,
        type=txn_type,
        amount=amount,
        balance_after=round(balance_after, 2),
        description=description,
    )
    db.session.add(txn)
    return txn


def _send_cashout_email(user, amount):
    """Send cashout confirmation email (best-effort)."""
    if not user.email:
        return
    try:
        from app.services.email import send_email

        now = datetime.utcnow()
        body = (
            f"Hi {user.username},\n\n"
            f"You've cashed out ${amount:.2f} on {now:%Y-%m-%d} at {now:%H:%M}.\n\n"
            f"Show this email to collect your payout!\n\n"
            f"— Felker Family Hub"
        )
        send_email(
            to=user.email,
            subject="Felker Family Hub - Cash Out Confirmation",
            body=body,
        )
    except Exception as e:
        current_app.logger.error("Cashout email failed: %s", e)


# ── page route ───────────────────────────────────────────────────────

@bank_bp.route("/bank")
def bank_page():
    """Render the bank page."""
    user_id = session.get("current_user_id")
    if not user_id:
        return render_template("bank.html", active_nav="bank")
    return render_template("bank.html", active_nav="bank")


# ── API routes ───────────────────────────────────────────────────────

@bank_bp.route("/api/bank/overview")
def bank_overview():
    """Return full bank overview JSON for the current user."""
    result = _require_login()
    if result[1] is None:
        return result[0], 401

    user_id, user = result
    account = _get_or_create_account(user_id)
    # Credit any accrued interest into cash_balance before computing totals
    credit_interest(user_id)
    db.session.refresh(account)

    deposits = _active_deposits(user_id)
    unlocked = _unlocked_deposits(user_id)

    total_savings = sum(d.amount for d in deposits)
    unlocked_total = sum(d.amount for d in unlocked)
    cashout_available = round(account.cash_balance + unlocked_total, 2)

    # Current savings goal
    goal = SavingsGoal.query.filter_by(user_id=user_id, completed_at=None).first()

    # Interest projection
    weekly_rate = _bank_cfg("interest_rate")
    yearly_projection = round(total_savings * weekly_rate * 52, 2)

    # Last 8 allowance transactions, newest first
    allowance_history = Transaction.query.filter_by(
        user_id=user_id, type=Transaction.TYPE_ALLOWANCE
    ).order_by(Transaction.created_at.desc()).limit(8).all()

    # Goal progress: earnings since goal was set (baseline snapshot taken at creation)
    # Never reduced by cashout; reduced by new locked savings deposits
    current_total = account.cash_balance + account.total_cashed_out + unlocked_total
    goal_progress = round(
        max(0.0, current_total - (goal.progress_baseline if goal else 0.0)), 2
    )

    return jsonify({
        "account": account.to_dict(),
        "cashout_available": cashout_available,
        "total_savings": round(total_savings, 2),
        "unlocked_savings": round(unlocked_total, 2),
        "yearly_projection": yearly_projection,
        "deposits": [d.to_dict() for d in deposits],
        "goal": goal.to_dict() if goal else None,
        "goal_progress": goal_progress,
        "savings_max": _bank_cfg("savings_max"),
        "savings_deposit_min": _bank_cfg("savings_deposit_min"),
        "cashout_min": _bank_cfg("cashout_min"),
        "fire_mode": user.fire_mode,
        "allowance": round(user.allowance or 0, 2),
        "allowance_history": [
            {
                "amount": round(t.amount, 2),
                "created_at": t.created_at.isoformat(),
                "description": t.description or "",
            }
            for t in allowance_history
        ],
    })


@bank_bp.route("/api/bank/ticker")
def bank_ticker():
    """Return ticker data for the nav bar interest display."""
    user_id = session.get("current_user_id")
    if not user_id:
        return jsonify({
            "total_active_savings": 0.0,
            "weekly_rate": _bank_cfg("interest_rate"),
            "last_interest_credit": None,
            "accrued_interest": 0.0,
            "cash_balance": 0.0,
            "unlocked_savings": 0.0,
        })
    return jsonify(get_ticker_data(user_id))


@bank_bp.route("/bank/cashout", methods=["POST"])
def cashout():
    """Cash out: cash balance first, then unlocked savings deposits."""
    result = _require_login()
    if result[1] is None:
        return result[0], 401

    user_id, user = result
    account = _get_or_create_account(user_id)
    # Credit any accrued interest before cashout so it's included in the total
    credit_interest(user_id)
    db.session.refresh(account)

    unlocked = _unlocked_deposits(user_id)

    unlocked_total = sum(d.amount for d in unlocked)
    total = round(account.cash_balance + unlocked_total, 2)
    cashout_min = _bank_cfg("cashout_min")

    if total < cashout_min:
        return jsonify({
            "error": f"Minimum cashout is ${cashout_min:.2f}. "
                     f"You have ${total:.2f} available."
        }), 400

    # Draw from cash first
    cash_portion = account.cash_balance
    account.cash_balance = 0.0

    # Then withdraw unlocked savings
    savings_portion = 0.0
    for deposit in unlocked:
        deposit.withdrawn = True
        deposit.withdrawn_at = datetime.utcnow()
        savings_portion += deposit.amount

    account.total_cashed_out += total

    _record_transaction(
        user_id, Transaction.TYPE_CASHOUT, -total, 0.0,
        f"Cashout: ${cash_portion:.2f} cash + ${savings_portion:.2f} savings",
    )
    db.session.commit()

    _send_cashout_email(user, total)

    # Check cashout achievements
    from app.services.achievements import check_achievements
    achievements = check_achievements(user_id, "cashout")

    return jsonify({
        "cashed_out": round(total, 2),
        "cash_portion": round(cash_portion, 2),
        "savings_portion": round(savings_portion, 2),
        "account": account.to_dict(),
        "achievements": achievements,
    })


@bank_bp.route("/bank/savings/deposit", methods=["POST"])
def savings_deposit():
    """Move cash into a new savings deposit with lock period."""
    result = _require_login()
    if result[1] is None:
        return result[0], 401

    user_id, user = result
    data = request.get_json(silent=True) or {}
    amount = data.get("amount")

    if amount is None:
        return jsonify({"error": "Amount is required"}), 400
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid amount"}), 400

    deposit_min = _bank_cfg("savings_deposit_min")
    if amount < deposit_min:
        return jsonify({"error": f"Minimum deposit is ${deposit_min:.2f}"}), 400

    account = _get_or_create_account(user_id)
    if amount > account.cash_balance:
        return jsonify({
            "error": f"Insufficient cash. You have ${account.cash_balance:.2f}."
        }), 400

    # Check savings max
    savings_max = _bank_cfg("savings_max")
    current_savings = sum(d.amount for d in _active_deposits(user_id))
    if current_savings + amount > savings_max:
        room = max(0, savings_max - current_savings)
        return jsonify({
            "error": f"Savings max is ${savings_max:.2f}. "
                     f"You can deposit up to ${room:.2f} more."
        }), 400

    # Create deposit
    now = datetime.utcnow()
    lock_days = int(_bank_cfg("savings_lock_days"))
    weekly_rate = _bank_cfg("interest_rate")

    deposit = SavingsDeposit(
        user_id=user_id,
        amount=amount,
        deposited_at=now,
        lock_until=now + timedelta(days=lock_days),
        interest_rate=weekly_rate,
    )
    db.session.add(deposit)

    account.cash_balance -= amount
    # Set last_interest_credit if this is the first deposit
    if not account.last_interest_credit:
        account.last_interest_credit = now

    _record_transaction(
        user_id, Transaction.TYPE_SAVINGS_DEPOSIT, -amount,
        round(account.cash_balance, 2),
        f"Deposit ${amount:.2f} to savings (locked {lock_days} days)",
    )
    db.session.commit()

    # Check deposit achievements
    from app.services.achievements import check_achievements
    achievements = check_achievements(user_id, "savings_deposit")

    return jsonify({
        "deposit": deposit.to_dict(),
        "account": account.to_dict(),
        "achievements": achievements,
    }), 201


@bank_bp.route("/bank/savings/withdraw/<int:deposit_id>", methods=["POST"])
def savings_withdraw(deposit_id):
    """Withdraw an unlocked savings deposit (direct cashout)."""
    result = _require_login()
    if result[1] is None:
        return result[0], 401

    user_id, user = result
    deposit = db.session.get(SavingsDeposit, deposit_id)

    if not deposit or deposit.user_id != user_id:
        return jsonify({"error": "Deposit not found"}), 404

    if deposit.withdrawn:
        return jsonify({"error": "Deposit already withdrawn"}), 400

    if deposit.is_locked:
        return jsonify({"error": "Deposit is still locked"}), 400

    account = _get_or_create_account(user_id)

    deposit.withdrawn = True
    deposit.withdrawn_at = datetime.utcnow()
    account.total_cashed_out += deposit.amount

    _record_transaction(
        user_id, Transaction.TYPE_SAVINGS_WITHDRAWAL, -deposit.amount,
        round(account.cash_balance, 2),
        f"Savings withdrawal: ${deposit.amount:.2f} (direct cashout)",
    )
    db.session.commit()

    _send_cashout_email(user, deposit.amount)

    return jsonify({
        "withdrawn": round(deposit.amount, 2),
        "deposit": deposit.to_dict(),
        "account": account.to_dict(),
    })


@bank_bp.route("/bank/savings/goal", methods=["POST"])
def savings_goal():
    """Create or update the user's savings goal."""
    result = _require_login()
    if result[1] is None:
        return result[0], 401

    user_id, _ = result
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    target = data.get("target_amount")

    if not name:
        return jsonify({"error": "Goal name is required"}), 400
    try:
        target = float(target)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid target amount"}), 400
    if target <= 0:
        return jsonify({"error": "Target must be positive"}), 400

    # Replace existing active goal (one at a time)
    existing = SavingsGoal.query.filter_by(
        user_id=user_id, completed_at=None
    ).first()

    if existing:
        # Edit: only rename / retarget — baseline stays so progress isn't reset
        existing.name = name
        existing.target_amount = target
        goal = existing
    else:
        # New goal: snapshot current earnings as baseline
        account = _get_or_create_account(user_id)
        unlocked_now = sum(d.amount for d in _unlocked_deposits(user_id))
        baseline = account.cash_balance + account.total_cashed_out + unlocked_now
        goal = SavingsGoal(
            user_id=user_id,
            name=name,
            target_amount=target,
            progress_baseline=round(baseline, 2),
        )
        db.session.add(goal)

    db.session.commit()
    return jsonify(goal.to_dict()), 201


@bank_bp.route("/bank/savings/goal/clear", methods=["POST"])
def clear_savings_goal():
    """Mark the current savings goal as completed (kid is ready to reset)."""
    result = _require_login()
    if result[1] is None:
        return result[0], 401

    user_id, _ = result
    goal = SavingsGoal.query.filter_by(user_id=user_id, completed_at=None).first()
    if not goal:
        return jsonify({"error": "No active goal"}), 404

    goal.completed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"cleared": True})


@bank_bp.route("/bank/savings/goal", methods=["DELETE"])
def delete_savings_goal():
    """Abandon (delete) the current active savings goal."""
    result = _require_login()
    if result[1] is None:
        return result[0], 401

    user_id, _ = result
    goal = SavingsGoal.query.filter_by(user_id=user_id, completed_at=None).first()
    if not goal:
        return jsonify({"error": "No active goal"}), 404

    db.session.delete(goal)
    db.session.commit()
    return jsonify({"deleted": True})


@bank_bp.route("/bank/transactions")
def transaction_history():
    """Paginated transaction history for the current user."""
    result = _require_login()
    if result[1] is None:
        return result[0], 401

    user_id, _ = result
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)  # cap

    query = Transaction.query.filter_by(user_id=user_id).order_by(
        Transaction.created_at.desc()
    )
    total = query.count()
    transactions = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        "transactions": [t.to_dict() for t in transactions],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": (total + per_page - 1) // per_page,
    })


@bank_bp.route("/bank/stats")
def bank_stats():
    """Historical stats for the current user."""
    result = _require_login()
    if result[1] is None:
        return result[0], 401

    user_id, _ = result
    account = _get_or_create_account(user_id)

    return jsonify({
        "total_cashed_out": round(account.total_cashed_out, 2),
        "total_interest_earned": round(account.total_interest_earned, 2),
        "cash_balance": round(account.cash_balance, 2),
        "total_savings": round(
            sum(d.amount for d in _active_deposits(user_id)), 2
        ),
    })
