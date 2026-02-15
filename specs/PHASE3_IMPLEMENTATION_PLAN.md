# Phase 3: Bank & Savings — Implementation Plan

> **Status:** PHASE 3 COMPLETE (2026-02-14). All sub-phases 3A–3E done. 135 tests passing.

## Context

Phase 2 (Calendar Dashboard & Streaks) is complete with 71 passing tests. Phase 3 adds the in-app bank system — the most exciting feature for the kids. It replaces email-based allowance reporting with real-time cash accounts, savings with per-deposit lock timers, a continuously ticking interest display, cashout flow with email confirmation, and transaction history.

## Sub-Phases (5 incremental steps)

---

### 3A: Data Models & Migration — COMPLETE

**Done (2026-02-14):**
- Created `app/models/bank.py` — 4 models: BankAccount, SavingsDeposit, Transaction, SavingsGoal
- Registered in `app/models/__init__.py`
- Alembic migration `62035d498409` (down_revision = `c19e0605deb4`) — creates bank_account, savings_deposit, transaction, savings_goal tables
- Migration applied, all 71 existing tests still pass

---

### 3B: Services (Email + Interest) — COMPLETE

**Done (2026-02-14):**
- Created `app/services/email.py` — Mailgun wrapper using `current_app.config`, dry-run when keys missing
- Created `app/services/interest.py` — `calculate_interest()`, `credit_interest()`, `get_ticker_data()`
- Created `app/services/allowance.py` — `calculate_allowance()` with 100/50/0 tier rule
- Created `tests/unit/test_allowance.py` (10 tests) and `tests/unit/test_interest.py` (11 tests)
- 92 tests all passing (71 existing + 21 new)

---

### 3C: Bank Blueprint (API endpoints) — COMPLETE

**Done (2026-02-14):**
- Created `app/blueprints/bank.py` with all 9 routes: `/bank`, `/api/bank/overview`, `/api/bank/ticker`, `/bank/cashout`, `/bank/savings/deposit`, `/bank/savings/withdraw/<id>`, `/bank/savings/goal`, `/bank/transactions`, `/bank/stats`
- Helpers: `_get_or_create_account()`, `_require_login()`, `_active_deposits()`, `_unlocked_deposits()`, `_record_transaction()`, `_send_cashout_email()`
- Cashout: draws cash first, then unlocked savings; sends Mailgun email
- Savings deposit: validates min/max, creates locked deposit with rate snapshot
- Savings withdraw: validates unlocked + ownership, direct cashout with email
- Registered `bank_bp` in `app/__init__.py`
- Created `tests/api/test_bank_api.py` (37 tests covering all endpoints + edge cases)
- 129 tests all passing (92 existing + 37 new)

---

### 3D: Frontend (Template + CSS + Alpine.js + Ticker)

**Create** `app/templates/bank.html` — extends `base.html`:
- Alpine.js component `bankApp` with `x-init="loadData()"`
- **Cashout section** (top): large "$XX.XX available" display, "Cash Out" button, confirmation modal
- **Cash balance** card
- **Savings overview** card: total with real-time ticker (6 decimals via requestAnimationFrame), yearly projection, "Deposit" button + amount input
- **Savings deposits grid**: each deposit rendered as a crystal/gem:
  - CSS-only gems with gradients, glow effects, faceted shapes
  - Locked: frosted overlay + countdown timer (days/hours/minutes)
  - Unlocked: warm golden glow, pulsing animation, "Withdraw" button
  - Size scales with amount ($1-10 small, $10-50 medium, $50+ large)
- **Savings goal** card: progress bar if goal set, "Set Goal" form
- **Weekly report** card: last week's completion % + allowance earned
- **Stats** card: total cashed out, total interest earned
- **History tab**: toggle between main view and transaction ledger

**Add CSS** to `app/static/css/style.css`:
- `.bank-*` classes for all bank components
- Crystal/gem visualization (CSS shapes, gradients, frost overlay, glow animations)
- Cashout confirmation modal (dark overlay, glassmorphic card)
- Transaction ledger styles

**Modify** `app/templates/base.html` — wire up nav bar ticker:
- In Alpine `app` component: fetch `/api/bank/ticker` on init + every 30s
- Calculate client-side interest via requestAnimationFrame
- Update `tickerDisplay` with "+$X.XXXXXX"
- Only tick when user is logged in (check `current_user` template var)

**Verify**: Manual browser testing — page loads, ticker ticks, deposits display, cashout flow works

---

### 3E: Weekly Reset Integration

**Modify** `app/blueprints/chores.py` `_weekly_archive()` — after existing archive+rotate+streak logic, add:
1. For each user with chores: calculate completion %, determine allowance tier
2. Get or create BankAccount, deposit allowance to cash_balance, record `allowance` Transaction
3. For each user with active savings: call `credit_interest()` from interest service
4. Expire TrustedIPs older than `TRUSTED_IP_EXPIRY_DAYS`

Uses `app/services/allowance.py` for tier calculation and `app/services/interest.py` for interest crediting.

**Verify**: Unit tests for weekly reset with bank integration (allowance deposit, interest credit, IP expiry)

---

## Files Summary

| Action | File |
|--------|------|
| **Create** | `app/models/bank.py` |
| **Create** | `app/services/email.py` |
| **Create** | `app/services/interest.py` |
| **Create** | `app/services/allowance.py` |
| **Create** | `app/blueprints/bank.py` |
| **Create** | `app/templates/bank.html` |
| **Create** | `tests/api/test_bank_api.py` |
| **Create** | `tests/unit/test_interest.py` |
| **Create** | `tests/unit/test_allowance.py` |
| **Create** | `tests/unit/test_weekly_reset_bank.py` |
| **Create** | migration file (auto-generated) |
| **Modify** | `app/models/__init__.py` (add bank imports) |
| **Modify** | `app/__init__.py` (register bank_bp) |
| **Modify** | `app/static/css/style.css` (bank page + crystal styles) |
| **Modify** | `app/templates/base.html` (wire ticker) |
| **Modify** | `app/blueprints/chores.py` (extend weekly reset) |

## Key Design Decisions

1. **No SocketIO for nav ticker** — Alpine.js polling `/api/bank/ticker` every 30s + client-side requestAnimationFrame is simpler and sufficient. SocketIO reserved for future bank page enhancements.
2. **Lazy BankAccount creation** — accounts created on first allowance deposit or manual access, not upfront for all users.
3. **Crystal visualization via CSS only** — no canvas/SVG needed. CSS gradients + clip-path + glow + animations create impressive gem effects.
4. **Email service extracted** — new `app/services/email.py` replaces direct `reporting.py` usage for bank emails. Reporting.py left intact for V1 compatibility.

## Verification

1. `pytest tests/` — all existing 71 tests still pass + new bank tests
2. `flask db upgrade` — migration applies cleanly
3. Manual test: login → bank page → deposit to savings → watch ticker → wait for unlock → cashout → verify email
4. Weekly reset test: trigger manual reset → verify allowance deposited + interest credited
