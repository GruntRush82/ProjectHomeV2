"""Bank models — BankAccount, SavingsDeposit, Transaction, SavingsGoal."""

from datetime import datetime

from app.extensions import db


class BankAccount(db.Model):
    """One record per user. Created lazily on first allowance deposit."""

    __tablename__ = "bank_account"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False
    )
    cash_balance = db.Column(db.Float, nullable=False, default=0.0)
    total_cashed_out = db.Column(db.Float, nullable=False, default=0.0)
    total_interest_earned = db.Column(db.Float, nullable=False, default=0.0)
    last_interest_credit = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship(
        "User", backref=db.backref("bank_account", uselist=False)
    )

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "cash_balance": round(self.cash_balance, 2),
            "total_cashed_out": round(self.total_cashed_out, 2),
            "total_interest_earned": round(self.total_interest_earned, 2),
            "last_interest_credit": (
                self.last_interest_credit.isoformat()
                if self.last_interest_credit
                else None
            ),
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<BankAccount user_id={self.user_id} cash=${self.cash_balance:.2f}>"


class SavingsDeposit(db.Model):
    """One row per savings deposit. Interest accrues until withdrawn."""

    __tablename__ = "savings_deposit"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    deposited_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    lock_until = db.Column(db.DateTime, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    withdrawn = db.Column(db.Boolean, nullable=False, default=False)
    withdrawn_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship(
        "User", backref=db.backref("savings_deposits", lazy=True)
    )

    @property
    def is_locked(self):
        return not self.withdrawn and datetime.utcnow() < self.lock_until

    @property
    def is_unlocked(self):
        return not self.withdrawn and datetime.utcnow() >= self.lock_until

    def to_dict(self):
        now = datetime.utcnow()
        locked = not self.withdrawn and now < self.lock_until
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": round(self.amount, 2),
            "deposited_at": self.deposited_at.isoformat(),
            "lock_until": self.lock_until.isoformat(),
            "interest_rate": self.interest_rate,
            "locked": locked,
            "withdrawn": self.withdrawn,
            "withdrawn_at": (
                self.withdrawn_at.isoformat() if self.withdrawn_at else None
            ),
            "lock_seconds_remaining": (
                max(0, int((self.lock_until - now).total_seconds()))
                if locked
                else 0
            ),
            "lock_total_seconds": max(
                0,
                int((self.lock_until - self.deposited_at).total_seconds()),
            ),
            "melt_percent": (
                100.0
                if not locked
                else round(
                    min(
                        100.0,
                        max(
                            0.0,
                            (now - self.deposited_at).total_seconds()
                            / max(
                                1,
                                (self.lock_until - self.deposited_at).total_seconds(),
                            )
                            * 100,
                        ),
                    ),
                    1,
                )
            ),
        }

    def __repr__(self):
        status = "locked" if self.is_locked else ("withdrawn" if self.withdrawn else "unlocked")
        return f"<SavingsDeposit id={self.id} ${self.amount:.2f} {status}>"


class Transaction(db.Model):
    """Immutable ledger record. Every monetary event produces one row."""

    __tablename__ = "transaction"

    TYPE_ALLOWANCE = "allowance"
    TYPE_CASHOUT = "cashout"
    TYPE_SAVINGS_DEPOSIT = "savings_deposit"
    TYPE_SAVINGS_WITHDRAWAL = "savings_withdrawal"
    TYPE_INTEREST = "interest"
    TYPE_MISSION_REWARD = "mission_reward"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    type = db.Column(db.String(30), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    balance_after = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(300), nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship(
        "User", backref=db.backref("transactions", lazy=True)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "amount": round(self.amount, 2),
            "balance_after": round(self.balance_after, 2),
            "description": self.description,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return (
            f"<Transaction id={self.id} type={self.type} "
            f"amount={self.amount:+.2f}>"
        )


class SavingsGoal(db.Model):
    """Optional named savings target for a user."""

    __tablename__ = "savings_goal"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship(
        "User", backref=db.backref("savings_goals", lazy=True)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "target_amount": round(self.target_amount, 2),
            "created_at": self.created_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }

    def __repr__(self):
        return f"<SavingsGoal id={self.id} name={self.name!r}>"
