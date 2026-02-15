"""Unit tests for weekly reset bank integration (allowance deposit, interest, IP expiry)."""

from datetime import date, datetime, timedelta

import pytest

from app.extensions import db
from app.models.bank import BankAccount, SavingsDeposit, Transaction
from app.models.chore import Chore, ChoreHistory
from app.models.security import TrustedIP
from app.models.user import User


@pytest.fixture
def reset_users(app, db):
    """Create users with allowances and chores for reset testing."""
    with app.app_context():
        kid1 = User(username="ResetKid1", allowance=15.0)
        kid2 = User(username="ResetKid2", allowance=20.0)
        db.session.add_all([kid1, kid2])
        db.session.commit()

        # kid1: 2 chores, both completed → 100% → full $15
        for day in ["Monday", "Wednesday"]:
            db.session.add(Chore(
                description=f"Kid1 {day}",
                user_id=kid1.id,
                day=day,
                completed=True,
            ))

        # kid2: 2 chores, 1 completed → 50% → half $10
        db.session.add(Chore(
            description="Kid2 Mon",
            user_id=kid2.id,
            day="Monday",
            completed=True,
        ))
        db.session.add(Chore(
            description="Kid2 Wed",
            user_id=kid2.id,
            day="Wednesday",
            completed=False,
        ))
        db.session.commit()

        yield {"kid1": kid1, "kid2": kid2}


def _run_weekly_archive(app):
    """Run the weekly archive within app context."""
    with app.app_context():
        from app.blueprints.chores import _weekly_archive
        # Clear any existing history for today to allow re-running
        ChoreHistory.query.filter_by(date=date.today()).delete()
        db.session.commit()
        _weekly_archive(send_reports=False)


class TestAllowanceDeposit:

    def test_full_completion_deposits_full_allowance(self, app, reset_users):
        _run_weekly_archive(app)
        with app.app_context():
            kid1 = reset_users["kid1"]
            account = BankAccount.query.filter_by(user_id=kid1.id).first()
            assert account is not None
            assert account.cash_balance == 15.0

    def test_half_completion_deposits_half_allowance(self, app, reset_users):
        _run_weekly_archive(app)
        with app.app_context():
            kid2 = reset_users["kid2"]
            account = BankAccount.query.filter_by(user_id=kid2.id).first()
            assert account is not None
            assert account.cash_balance == 10.0

    def test_creates_bank_account_if_missing(self, app, reset_users):
        with app.app_context():
            # Verify no account exists before reset
            assert BankAccount.query.filter_by(
                user_id=reset_users["kid1"].id
            ).first() is None

        _run_weekly_archive(app)

        with app.app_context():
            assert BankAccount.query.filter_by(
                user_id=reset_users["kid1"].id
            ).first() is not None

    def test_records_allowance_transaction(self, app, reset_users):
        _run_weekly_archive(app)
        with app.app_context():
            txn = Transaction.query.filter_by(
                user_id=reset_users["kid1"].id,
                type=Transaction.TYPE_ALLOWANCE,
            ).first()
            assert txn is not None
            assert txn.amount == 15.0
            assert "full" in txn.description


class TestInterestOnReset:

    def test_credits_interest_on_savings(self, app, db, reset_users):
        with app.app_context():
            kid = reset_users["kid1"]
            now = datetime.utcnow()
            account = BankAccount(
                user_id=kid.id,
                cash_balance=0,
                last_interest_credit=now - timedelta(weeks=1),
            )
            db.session.add(account)
            deposit = SavingsDeposit(
                user_id=kid.id,
                amount=100.0,
                deposited_at=now - timedelta(weeks=2),
                lock_until=now + timedelta(days=14),
                interest_rate=0.05,
            )
            db.session.add(deposit)
            db.session.commit()

        _run_weekly_archive(app)

        with app.app_context():
            kid = reset_users["kid1"]
            account = BankAccount.query.filter_by(user_id=kid.id).first()
            # Should have allowance ($15) + interest (~$5)
            assert account.cash_balance > 19.0
            assert account.total_interest_earned > 4.0

            interest_txn = Transaction.query.filter_by(
                user_id=kid.id,
                type=Transaction.TYPE_INTEREST,
            ).first()
            assert interest_txn is not None


class TestIPExpiry:

    def test_expires_old_ips(self, app, db):
        with app.app_context():
            old = TrustedIP(
                ip_address="1.2.3.4",
                trusted_at=datetime.utcnow() - timedelta(days=10),
                last_seen=datetime.utcnow() - timedelta(days=10),
            )
            recent = TrustedIP(
                ip_address="5.6.7.8",
                trusted_at=datetime.utcnow() - timedelta(days=1),
                last_seen=datetime.utcnow() - timedelta(days=1),
            )
            db.session.add_all([old, recent])
            db.session.commit()

        _run_weekly_archive(app)

        with app.app_context():
            remaining = TrustedIP.query.all()
            ips = [t.ip_address for t in remaining]
            assert "1.2.3.4" not in ips
            assert "5.6.7.8" in ips
