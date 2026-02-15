"""API tests for the bank blueprint."""

from datetime import datetime, timedelta

import pytest

from app.extensions import db
from app.models.bank import BankAccount, SavingsDeposit, SavingsGoal, Transaction
from app.models.user import User


@pytest.fixture
def bank_kid(app, db, sample_users, logged_in_client):
    """A logged-in kid with a bank account containing $50 cash."""
    kid = sample_users["kid1"]
    kid.email = "kid1@test.com"
    account = BankAccount(
        user_id=kid.id,
        cash_balance=50.0,
        last_interest_credit=datetime.utcnow(),
    )
    db.session.add(account)
    db.session.commit()
    client = logged_in_client(user_id=kid.id)
    return {"client": client, "user": kid, "account": account}


@pytest.fixture
def bank_kid_with_deposits(app, db, bank_kid):
    """Bank kid with both locked and unlocked savings deposits."""
    now = datetime.utcnow()
    kid = bank_kid["user"]

    locked = SavingsDeposit(
        user_id=kid.id,
        amount=25.0,
        deposited_at=now - timedelta(days=5),
        lock_until=now + timedelta(days=25),
        interest_rate=0.05,
    )
    unlocked = SavingsDeposit(
        user_id=kid.id,
        amount=10.0,
        deposited_at=now - timedelta(days=45),
        lock_until=now - timedelta(days=1),
        interest_rate=0.05,
    )
    db.session.add_all([locked, unlocked])
    db.session.commit()

    bank_kid["locked_deposit"] = locked
    bank_kid["unlocked_deposit"] = unlocked
    return bank_kid


# ── Overview ─────────────────────────────────────────────────────────

class TestBankOverview:

    def test_requires_login(self, auth_client):
        resp = auth_client.get("/api/bank/overview")
        assert resp.status_code == 401

    def test_returns_account_data(self, bank_kid):
        resp = bank_kid["client"].get("/api/bank/overview")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["account"]["cash_balance"] == 50.0
        assert data["cashout_available"] == 50.0
        assert data["total_savings"] == 0.0

    def test_includes_unlocked_in_cashout_available(self, bank_kid_with_deposits):
        resp = bank_kid_with_deposits["client"].get("/api/bank/overview")
        data = resp.get_json()
        # $50 cash + $10 unlocked = $60
        assert data["cashout_available"] == 60.0
        assert data["total_savings"] == 35.0
        assert data["unlocked_savings"] == 10.0

    def test_includes_config_values(self, bank_kid):
        resp = bank_kid["client"].get("/api/bank/overview")
        data = resp.get_json()
        assert "savings_max" in data
        assert "savings_deposit_min" in data
        assert "cashout_min" in data


# ── Ticker ───────────────────────────────────────────────────────────

class TestBankTicker:

    def test_returns_zeros_when_not_logged_in(self, auth_client):
        resp = auth_client.get("/api/bank/ticker")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_active_savings"] == 0.0

    def test_returns_ticker_with_savings(self, bank_kid_with_deposits):
        resp = bank_kid_with_deposits["client"].get("/api/bank/ticker")
        data = resp.get_json()
        assert data["total_active_savings"] == 35.0
        assert data["weekly_rate"] == 0.05
        assert data["last_interest_credit"] is not None


# ── Cashout ──────────────────────────────────────────────────────────

class TestCashout:

    def test_requires_login(self, auth_client):
        resp = auth_client.post("/bank/cashout")
        assert resp.status_code == 401

    def test_cashout_cash_only(self, bank_kid):
        resp = bank_kid["client"].post("/bank/cashout")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["cashed_out"] == 50.0
        assert data["cash_portion"] == 50.0
        assert data["savings_portion"] == 0.0
        assert data["account"]["cash_balance"] == 0.0

    def test_cashout_cash_plus_unlocked(self, bank_kid_with_deposits):
        resp = bank_kid_with_deposits["client"].post("/bank/cashout")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["cashed_out"] == 60.0
        assert data["cash_portion"] == 50.0
        assert data["savings_portion"] == 10.0

    def test_cashout_records_transaction(self, bank_kid):
        bank_kid["client"].post("/bank/cashout")
        txn = Transaction.query.filter_by(
            user_id=bank_kid["user"].id,
            type=Transaction.TYPE_CASHOUT,
        ).first()
        assert txn is not None
        assert txn.amount == -50.0

    def test_cashout_updates_total(self, bank_kid):
        bank_kid["client"].post("/bank/cashout")
        acct = BankAccount.query.filter_by(user_id=bank_kid["user"].id).first()
        assert acct.total_cashed_out == 50.0

    def test_cashout_below_minimum(self, app, db, sample_users, logged_in_client):
        kid = sample_users["kid1"]
        acct = BankAccount(user_id=kid.id, cash_balance=0.50)
        db.session.add(acct)
        db.session.commit()
        client = logged_in_client(user_id=kid.id)
        resp = client.post("/bank/cashout")
        assert resp.status_code == 400
        assert "Minimum" in resp.get_json()["error"]


# ── Savings Deposit ──────────────────────────────────────────────────

class TestSavingsDeposit:

    def test_requires_login(self, auth_client):
        resp = auth_client.post("/bank/savings/deposit", json={"amount": 10})
        assert resp.status_code == 401

    def test_deposit_success(self, bank_kid):
        resp = bank_kid["client"].post(
            "/bank/savings/deposit", json={"amount": 20}
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["deposit"]["amount"] == 20.0
        assert data["deposit"]["locked"] is True
        assert data["account"]["cash_balance"] == 30.0

    def test_deposit_records_transaction(self, bank_kid):
        bank_kid["client"].post("/bank/savings/deposit", json={"amount": 10})
        txn = Transaction.query.filter_by(
            user_id=bank_kid["user"].id,
            type=Transaction.TYPE_SAVINGS_DEPOSIT,
        ).first()
        assert txn is not None
        assert txn.amount == -10.0

    def test_deposit_below_minimum(self, bank_kid):
        resp = bank_kid["client"].post(
            "/bank/savings/deposit", json={"amount": 0.50}
        )
        assert resp.status_code == 400
        assert "Minimum" in resp.get_json()["error"]

    def test_deposit_insufficient_cash(self, bank_kid):
        resp = bank_kid["client"].post(
            "/bank/savings/deposit", json={"amount": 100}
        )
        assert resp.status_code == 400
        assert "Insufficient" in resp.get_json()["error"]

    def test_deposit_exceeds_savings_max(self, bank_kid):
        # Savings max is $100 by default, try to deposit more
        bank_kid["account"].cash_balance = 200.0
        db.session.commit()
        resp = bank_kid["client"].post(
            "/bank/savings/deposit", json={"amount": 150}
        )
        assert resp.status_code == 400
        assert "max" in resp.get_json()["error"].lower()

    def test_deposit_missing_amount(self, bank_kid):
        resp = bank_kid["client"].post(
            "/bank/savings/deposit", json={}
        )
        assert resp.status_code == 400


# ── Savings Withdraw ─────────────────────────────────────────────────

class TestSavingsWithdraw:

    def test_requires_login(self, auth_client):
        resp = auth_client.post("/bank/savings/withdraw/1")
        assert resp.status_code == 401

    def test_withdraw_unlocked(self, bank_kid_with_deposits):
        kid = bank_kid_with_deposits
        dep_id = kid["unlocked_deposit"].id
        resp = kid["client"].post(f"/bank/savings/withdraw/{dep_id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["withdrawn"] == 10.0
        assert data["deposit"]["withdrawn"] is True

    def test_withdraw_locked_fails(self, bank_kid_with_deposits):
        kid = bank_kid_with_deposits
        dep_id = kid["locked_deposit"].id
        resp = kid["client"].post(f"/bank/savings/withdraw/{dep_id}")
        assert resp.status_code == 400
        assert "locked" in resp.get_json()["error"].lower()

    def test_withdraw_records_transaction(self, bank_kid_with_deposits):
        kid = bank_kid_with_deposits
        dep_id = kid["unlocked_deposit"].id
        kid["client"].post(f"/bank/savings/withdraw/{dep_id}")
        txn = Transaction.query.filter_by(
            user_id=kid["user"].id,
            type=Transaction.TYPE_SAVINGS_WITHDRAWAL,
        ).first()
        assert txn is not None
        assert txn.amount == -10.0

    def test_withdraw_updates_total_cashed_out(self, bank_kid_with_deposits):
        kid = bank_kid_with_deposits
        dep_id = kid["unlocked_deposit"].id
        kid["client"].post(f"/bank/savings/withdraw/{dep_id}")
        acct = BankAccount.query.filter_by(user_id=kid["user"].id).first()
        assert acct.total_cashed_out == 10.0

    def test_withdraw_nonexistent(self, bank_kid):
        resp = bank_kid["client"].post("/bank/savings/withdraw/9999")
        assert resp.status_code == 404

    def test_withdraw_already_withdrawn(self, bank_kid_with_deposits):
        kid = bank_kid_with_deposits
        dep = kid["unlocked_deposit"]
        dep.withdrawn = True
        dep.withdrawn_at = datetime.utcnow()
        db.session.commit()
        resp = kid["client"].post(f"/bank/savings/withdraw/{dep.id}")
        assert resp.status_code == 400


# ── Savings Goal ─────────────────────────────────────────────────────

class TestSavingsGoal:

    def test_requires_login(self, auth_client):
        resp = auth_client.post(
            "/bank/savings/goal",
            json={"name": "Bike", "target_amount": 50},
        )
        assert resp.status_code == 401

    def test_create_goal(self, bank_kid):
        resp = bank_kid["client"].post(
            "/bank/savings/goal",
            json={"name": "Bike", "target_amount": 50},
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"] == "Bike"
        assert data["target_amount"] == 50.0

    def test_update_existing_goal(self, bank_kid):
        bank_kid["client"].post(
            "/bank/savings/goal",
            json={"name": "Bike", "target_amount": 50},
        )
        resp = bank_kid["client"].post(
            "/bank/savings/goal",
            json={"name": "Skateboard", "target_amount": 30},
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"] == "Skateboard"
        # Should only have 1 active goal
        goals = SavingsGoal.query.filter_by(
            user_id=bank_kid["user"].id, completed_at=None
        ).all()
        assert len(goals) == 1

    def test_goal_missing_name(self, bank_kid):
        resp = bank_kid["client"].post(
            "/bank/savings/goal",
            json={"target_amount": 50},
        )
        assert resp.status_code == 400

    def test_goal_invalid_target(self, bank_kid):
        resp = bank_kid["client"].post(
            "/bank/savings/goal",
            json={"name": "Bike", "target_amount": -10},
        )
        assert resp.status_code == 400


# ── Transaction History ──────────────────────────────────────────────

class TestTransactionHistory:

    def test_requires_login(self, auth_client):
        resp = auth_client.get("/bank/transactions")
        assert resp.status_code == 401

    def test_empty_history(self, bank_kid):
        resp = bank_kid["client"].get("/bank/transactions")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["transactions"] == []
        assert data["total"] == 0

    def test_returns_transactions(self, bank_kid):
        # Trigger a cashout to create a transaction
        bank_kid["client"].post("/bank/cashout")
        resp = bank_kid["client"].get("/bank/transactions")
        data = resp.get_json()
        assert data["total"] == 1
        assert data["transactions"][0]["type"] == "cashout"

    def test_pagination(self, app, db, bank_kid):
        # Create 25 transactions
        for i in range(25):
            db.session.add(Transaction(
                user_id=bank_kid["user"].id,
                type="allowance",
                amount=1.0,
                balance_after=float(i),
                description=f"test {i}",
            ))
        db.session.commit()

        resp = bank_kid["client"].get("/bank/transactions?page=1&per_page=10")
        data = resp.get_json()
        assert len(data["transactions"]) == 10
        assert data["total"] == 25
        assert data["pages"] == 3


# ── Stats ────────────────────────────────────────────────────────────

class TestBankStats:

    def test_requires_login(self, auth_client):
        resp = auth_client.get("/bank/stats")
        assert resp.status_code == 401

    def test_returns_stats(self, bank_kid):
        resp = bank_kid["client"].get("/bank/stats")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["cash_balance"] == 50.0
        assert data["total_cashed_out"] == 0.0
        assert data["total_interest_earned"] == 0.0
