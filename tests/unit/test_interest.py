"""Unit tests for interest calculation service."""

from datetime import datetime, timedelta

import pytest

from app.extensions import db
from app.models.bank import BankAccount, SavingsDeposit, Transaction
from app.models.user import User
from app.services.interest import (
    calculate_interest,
    credit_interest,
    get_ticker_data,
)


@pytest.fixture
def bank_user(app, db):
    """Create a user with a bank account and savings deposit."""
    with app.app_context():
        user = User(username="BankKid", allowance=15.0)
        db.session.add(user)
        db.session.commit()

        now = datetime.utcnow()
        account = BankAccount(
            user_id=user.id,
            cash_balance=10.0,
            last_interest_credit=now - timedelta(weeks=1),
            created_at=now - timedelta(weeks=2),
        )
        db.session.add(account)
        db.session.commit()

        deposit = SavingsDeposit(
            user_id=user.id,
            amount=100.0,
            deposited_at=now - timedelta(weeks=2),
            lock_until=now + timedelta(days=14),
            interest_rate=0.05,
        )
        db.session.add(deposit)
        db.session.commit()

        yield {"user": user, "account": account, "deposit": deposit}


class TestCalculateInterest:

    def test_no_account_returns_zero(self, app):
        with app.app_context():
            assert calculate_interest(9999) == 0.0

    def test_no_savings_returns_zero(self, app, db):
        with app.app_context():
            user = User(username="NoSavings")
            db.session.add(user)
            db.session.commit()
            account = BankAccount(
                user_id=user.id,
                last_interest_credit=datetime.utcnow(),
            )
            db.session.add(account)
            db.session.commit()
            assert calculate_interest(user.id) == 0.0

    def test_one_week_earns_weekly_rate(self, app, bank_user):
        with app.app_context():
            # $100 savings * 5% rate * 1 week elapsed = $5.00
            interest = calculate_interest(bank_user["user"].id)
            assert 4.9 < interest < 5.1  # ~$5, allowing for seconds of drift

    def test_partial_week_prorates(self, app, db):
        with app.app_context():
            user = User(username="PartialWeek")
            db.session.add(user)
            db.session.commit()

            now = datetime.utcnow()
            account = BankAccount(
                user_id=user.id,
                last_interest_credit=now - timedelta(days=1),
            )
            db.session.add(account)
            deposit = SavingsDeposit(
                user_id=user.id,
                amount=70.0,
                deposited_at=now - timedelta(days=5),
                lock_until=now + timedelta(days=25),
                interest_rate=0.05,
            )
            db.session.add(deposit)
            db.session.commit()

            # $70 * 5% / 7 days * 1 day = $0.50
            interest = calculate_interest(user.id)
            assert 0.45 < interest < 0.55


class TestCreditInterest:

    def test_credits_to_cash_balance(self, app, bank_user):
        with app.app_context():
            user_id = bank_user["user"].id
            old_cash = bank_user["account"].cash_balance

            credited = credit_interest(user_id)
            assert credited > 0

            account = BankAccount.query.filter_by(user_id=user_id).first()
            assert account.cash_balance == pytest.approx(old_cash + credited, abs=0.01)

    def test_records_transaction(self, app, bank_user):
        with app.app_context():
            user_id = bank_user["user"].id
            credit_interest(user_id)

            txn = Transaction.query.filter_by(
                user_id=user_id, type=Transaction.TYPE_INTEREST
            ).first()
            assert txn is not None
            assert txn.amount > 0
            assert "interest" in txn.description.lower()

    def test_updates_total_interest_earned(self, app, bank_user):
        with app.app_context():
            user_id = bank_user["user"].id
            old_total = bank_user["account"].total_interest_earned

            credited = credit_interest(user_id)

            account = BankAccount.query.filter_by(user_id=user_id).first()
            assert account.total_interest_earned == pytest.approx(
                old_total + credited, abs=0.01
            )

    def test_updates_last_interest_credit(self, app, bank_user):
        with app.app_context():
            user_id = bank_user["user"].id
            old_credit = bank_user["account"].last_interest_credit

            credit_interest(user_id)

            account = BankAccount.query.filter_by(user_id=user_id).first()
            assert account.last_interest_credit > old_credit

    def test_no_account_returns_zero(self, app):
        with app.app_context():
            assert credit_interest(9999) == 0.0


class TestGetTickerData:

    def test_returns_ticker_data_with_savings(self, app, bank_user):
        with app.app_context():
            data = get_ticker_data(bank_user["user"].id)
            assert data["total_active_savings"] == 100.0
            assert data["weekly_rate"] == 0.05
            assert data["last_interest_credit"] is not None
            assert data["accrued_interest"] > 0

    def test_returns_zeros_without_account(self, app):
        with app.app_context():
            data = get_ticker_data(9999)
            assert data["total_active_savings"] == 0.0
            assert data["accrued_interest"] == 0.0
