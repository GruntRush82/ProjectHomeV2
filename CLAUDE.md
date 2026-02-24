# Project Home V2 — Development Reference

This file covers the V2 codebase (branch `v2`). For deployment, SSH, and V1 production info, see `~/CLAUDE.md`.

## IMPORTANT — Do Not Touch the Droplet
**Never SSH to the droplet, push to remote, deploy, or modify anything on `68.183.192.133` unless the user explicitly asks.** All work is local only unless specifically requested.

## Quick Start

```bash
# Activate venv and run locally
source venv/bin/activate
python run.py              # Starts on http://0.0.0.0:5000
```

- **Branch:** `v2` (V1 stays live on `master`)
- **Specs:** `specs/V2_PLAN.md` (phased plan + session handoff log), `specs/DECISIONS.md` (92 finalized decisions)
- **Tests:** `pytest tests/` (312 tests, all passing — v1.0 complete)
- **DB:** SQLite at `instance/chores.db`. For a fresh DB: delete the file and run `python -c "from app import create_app; from app.extensions import db; app=create_app(); app.app_context().push(); db.create_all()"`
- **Seed production chores:** Pull V1 DB from droplet, map user IDs, insert into V2 DB (see session handoff log in V2_PLAN.md)

**IMPORTANT:** When starting a new session for V2 work, ALWAYS read `specs/V2_PLAN.md` first for current status and next steps.

## Environment (.env)

`run.py` loads `.env` via `python-dotenv`. The file is **NOT tracked in git**. Required variables:

```
MAILGUN_API_KEY=<key>
MAILGUN_DOMAIN=<sandbox domain>

# Google Calendar (Phase 2)
GOOGLE_SERVICE_ACCOUNT_JSON=/home/felke/google-service-account.json
GOOGLE_CALENDAR_ID=carlyfelker@gmail.com
```

**Google Calendar setup:**
- Service account JSON key at the path above (not tracked in git)
- `carlyfelker@gmail.com` calendar shared with the service account `client_email`
- Service gracefully degrades (returns empty events) if credentials missing or API fails

## V2 File Structure

```
app/
├── __init__.py              # App factory: create_app(testing=False)
├── config.py                # Config / TestConfig classes
├── extensions.py            # db, migrate, socketio, scheduler
├── blueprints/
│   ├── achievements.py      # Achievement notifications, catalog, profile page, icon/theme APIs
│   ├── auth.py              # PIN, IP trust, login, sessions
│   ├── bank.py              # Bank: cashout, savings, goals, transactions, stats, ticker
│   ├── calendar_bp.py       # Calendar dashboard, events CRUD, today API
│   ├── chores.py            # Chore CRUD, grid, archive, reset, streak + bank + XP integration
│   ├── grocery.py           # Grocery list CRUD, email
│   ├── missions.py          # Mission hub, training, testing, notifications, admin assign/approve
│   └── users.py             # User CRUD
├── models/
│   ├── __init__.py          # Model imports for Alembic discovery
│   ├── achievement.py       # Achievement (catalog), UserAchievement (per-user unlocks)
│   ├── user.py              # User (username, email, allowance, xp, level, icon, theme, streaks, fire_mode...)
│   ├── chore.py             # Chore, ChoreHistory
│   ├── bank.py              # BankAccount, SavingsDeposit, Transaction, SavingsGoal
│   ├── calendar.py          # CalendarEvent
│   ├── grocery.py           # GroceryItem
│   ├── mission.py           # Mission, MissionAssignment, MissionProgress
│   └── security.py          # TrustedIP, PinAttempt, AppConfig
├── services/
│   ├── __init__.py
│   ├── achievements.py      # Achievement checking engine (trigger-based unlock + XP grant)
│   ├── allowance.py         # Allowance tier calculation (100%→full, ≥50%→half, <50%→$0)
│   ├── email.py             # Mailgun wrapper (V2-native, dry-run when keys missing)
│   ├── google_cal.py        # Google Calendar API integration (service account, caching)
│   ├── interest.py          # Interest calculation, crediting, ticker data
│   ├── xp.py                # XP grant, level thresholds (10 levels), level-up detection
│   └── missions/            # Mission handler framework
│       ├── __init__.py      # Handler registry (MISSION_HANDLERS dict)
│       ├── base.py          # BaseMissionHandler ABC
│       ├── multiplication.py # Adaptive training, 3-level testing, mnemonic hints
│       └── piano.py         # Simple "I did it" → admin approval flow
├── scripts/
│   ├── migrate_v1_data.py   # One-time V1 data migration
│   ├── seed_achievements.py # Seed 14 achievement definitions (idempotent)
│   └── seed_missions.py     # Seed Multiplication Master + Piano Performance definitions
├── static/
│   ├── css/style.css        # Dark neon glassmorphic theme
│   ├── js/scripts.js        # Chore/grocery frontend logic
│   └── sounds/cheer.wav
└── templates/
    ├── base.html            # Base layout, bottom nav, Alpine.js idle timer, ticker, achievement notifications
    ├── bank.html            # Bank page: cashout, savings gems, goals, Fire Mode indicator
    ├── calendar.html        # Daily calendar dashboard (served at /calendar)
    ├── login.html           # User selection cards with level effects (served at /)
    ├── missions.html        # Mission hub: training, testing, numpad, celebration (served at /missions)
    ├── admin_missions.html  # Admin: assign missions, approve/reject piano (served at /admin/missions)
    ├── pin.html             # PIN entry pad (served at /pin)
    ├── profile.html         # Profile page: stats, icons, themes, achievement catalog (served at /profile)
    └── chore_tracker.html   # Chore grid SPA (served at /chores-page)

run.py                       # Entry point: socketio.run(app)
tests/
├── conftest.py              # Shared fixtures (app, db, client, auth_client, sample_users, etc.)
├── test_smoke.py            # 5 smoke tests
├── unit/
│   ├── test_achievement_models.py # 11 achievement model + seed tests
│   ├── test_achievement_service.py # 13 achievement engine tests
│   ├── test_allowance.py    # 10 allowance tier calculation tests
│   ├── test_interest.py     # 11 interest calculation/crediting tests
│   ├── test_mission_models.py     # 9 mission model tests
│   ├── test_multiplication_service.py  # 20 multiplication handler tests
│   ├── test_piano_service.py      # 7 piano handler + registry tests
│   ├── test_streaks.py      # 4 streak tracking unit tests
│   ├── test_xp_service.py   # 13 XP service tests (levels, grant, level-up)
│   └── test_weekly_reset_bank.py  # 6 weekly reset bank integration tests
└── api/
    ├── test_achievement_integration.py  # 11 gamification hook integration tests
    ├── test_achievements_api.py  # 8 achievement API tests (notifications, catalog)
    ├── test_auth.py         # 10 auth/PIN/IP-trust tests
    ├── test_bank_api.py     # 37 bank API tests (cashout, savings, goals, transactions)
    ├── test_calendar_api.py # 11 calendar API tests (today, events CRUD)
    ├── test_gamification_e2e.py  # 10 end-to-end gamification flow tests
    ├── test_level_visuals.py # 3 level/fire-mode data attribute tests
    ├── test_missions_api.py # 25 mission API tests (auth, CRUD, state, notifications, admin)
    ├── test_mission_integration.py  # 8 end-to-end mission flow tests
    ├── test_profile_api.py  # 14 profile API tests (icon, theme, level gating)
    ├── test_session.py      # 8 login/logout/session tests
    ├── test_chores_api.py   # Chore CRUD tests
    ├── test_grocery_api.py  # Grocery CRUD tests
    └── test_users_api.py    # User CRUD tests
```

## Database Models

**User:** id, username (unique), email, allowance, is_admin, icon, theme_color, xp, level, streak_current, streak_best, perfect_weeks_total, fire_mode

**Achievement:** id, name (unique), description, icon, category, requirement_type, requirement_value, xp_reward, tier, is_visible, display_order

**UserAchievement:** id, user_id (FK), achievement_id (FK), unlocked_at, notified. Unique constraint on (user_id, achievement_id)

**Chore:** id, description, completed, user_id (FK), day, rotation_type (static/rotating), rotation_order (JSON), base_user_id (FK)

**ChoreHistory:** id, chore_id (FK), username, date, completed, day, rotation_type

**GroceryItem:** id, item_name, added_by, created_at

**CalendarEvent:** id, title, description, event_date, event_time, created_by (FK→User), google_event_id, created_at

**TrustedIP:** id, ip_address (unique), trusted_at, last_seen

**PinAttempt:** id, ip_address, attempted_at, success

**BankAccount:** id, user_id (unique FK), cash_balance, total_cashed_out, total_interest_earned, last_interest_credit, created_at

**SavingsDeposit:** id, user_id (FK), amount, deposited_at, lock_until, interest_rate (snapshot), withdrawn, withdrawn_at. Properties: `is_locked`, `is_unlocked`

**Transaction:** id, user_id (FK), type (allowance/cashout/savings_deposit/savings_withdrawal/interest/mission_reward), amount, balance_after, description, created_at. Class constants: TYPE_ALLOWANCE, TYPE_CASHOUT, TYPE_SAVINGS_DEPOSIT, TYPE_SAVINGS_WITHDRAWAL, TYPE_INTEREST, TYPE_MISSION_REWARD

**SavingsGoal:** id, user_id (FK), name, target_amount, created_at, completed_at

**AppConfig:** id, key (unique), value — runtime key/value store with `AppConfig.get(key)` / `AppConfig.set(key, value)`

**Mission:** id, title, description, mission_type (multiplication/piano), config (JSON), reward_cash, reward_icon, created_at

**MissionAssignment:** id, mission_id (FK), user_id (FK), state (assigned/training/testing/completed/failed/pending_approval), current_level (0-3), notified, assigned_at, started_at, completed_at. State constants: STATE_ASSIGNED, STATE_TRAINING, STATE_TESTING, STATE_COMPLETED, STATE_FAILED, STATE_PENDING_APPROVAL

**MissionProgress:** id, assignment_id (FK), session_type (training/test), data (JSON), score, duration_seconds, created_at

## Routes

### Auth (auth.py)
| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Login page (user selection cards) |
| `/pin` | GET/POST | PIN entry + validation |
| `/session` | POST | Start session (sets `current_user_id`) |
| `/session/logout` | GET | End session, redirect to `/` |

**App-wide before_request:** `require_trusted_ip` — redirects untrusted IPs to `/pin`. Skips `/static`, `/pin`, `/favicon.ico`. Bypassed entirely if no PIN hash is configured.

### Bank (bank.py)
| Route | Method | Purpose |
|-------|--------|---------|
| `/bank` | GET | Render bank page (savings gems, cashout, goals) |
| `/api/bank/overview` | GET | JSON: cash, savings, deposits, goal, stats |
| `/api/bank/ticker` | GET | JSON: ticker data (savings, rate, accrued interest, cash_balance, unlocked_savings) for nav bar total-available display |
| `/bank/cashout` | POST | Cash out (cash first, then unlocked savings) + email |
| `/bank/savings/deposit` | POST | Move cash to locked savings deposit |
| `/bank/savings/withdraw/<id>` | POST | Withdraw unlocked savings deposit + email |
| `/bank/savings/goal` | POST | Create/update savings goal |
| `/bank/transactions` | GET | Paginated transaction history |
| `/bank/stats` | GET | JSON: total cashed out, total interest earned |

### Calendar (calendar_bp.py)
| Route | Method | Purpose |
|-------|--------|---------|
| `/calendar` | GET | Render daily calendar dashboard |
| `/api/calendar/today` | GET | JSON: today's chores, events, streaks, progress |
| `/calendar/events` | POST | Create local event (+ push to Google Calendar) |
| `/calendar/events/<id>` | DELETE | Delete local event (+ remove from Google) |

### Chores (chores.py)
| Route | Method | Purpose |
|-------|--------|---------|
| `/chores-page` | GET | Render chore grid |
| `/chores` | GET/POST | List all / create chore |
| `/chores/<id>` | GET/PUT/DELETE | Read / update / delete chore |
| `/chores/<id>/move` | PUT | Drag-drop move (change user/day) |
| `/chores/archive` | POST | Snapshot to history, reset completed |
| `/chores/reset` | POST | Full weekly cycle (archive + rotate) |
| `/archive` | GET | View history |
| `/chores/clear-archive` | DELETE | Clear history |

### Grocery (grocery.py)
| Route | Method | Purpose |
|-------|--------|---------|
| `/grocery` | GET/POST | List all / add item |
| `/grocery/<id>` | DELETE | Remove item |
| `/grocery/clear` | DELETE | Clear all |
| `/grocery/send` | POST | Email list via Mailgun |

### Missions (missions.py)
| Route | Method | Purpose |
|-------|--------|---------|
| `/missions` | GET | Render missions hub page |
| `/api/missions` | GET | List user's assignments (active + completed) |
| `/api/missions/<id>/progress` | GET | Progress summary for assignment |
| `/missions/<id>/start` | POST | Transition assigned → training |
| `/api/missions/<id>/train` | GET | Get training session (20 questions) |
| `/missions/<id>/train` | POST | Submit training results |
| `/api/missions/<id>/test` | GET | Get test for next level |
| `/missions/<id>/test` | POST | Submit test results (+ grant reward if L3 pass) |
| `/api/missions/notifications` | GET | Unnotified assignments |
| `/api/missions/notifications/dismiss` | POST | Mark notifications as seen |
| `/admin/missions` | GET | Render admin missions page |
| `/api/admin/missions` | GET | List all missions, assignments, users |
| `/api/admin/missions/assign` | POST | Assign mission to user |
| `/api/admin/missions/<id>/approve` | POST | Approve pending piano mission |
| `/api/admin/missions/<id>/reject` | POST | Reject → back to training |

### Users (users.py)
| Route | Method | Purpose |
|-------|--------|---------|
| `/users` | GET/POST | List all / create user |
| `/users/<id>` | DELETE | Delete user + cascade chores |

### Achievements & Profile (achievements.py)
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/achievements/notifications` | GET | Unnotified achievements (gold-first) |
| `/api/achievements/notifications/dismiss` | POST | Mark achievement(s) as notified |
| `/api/achievements/catalog` | GET | All 14 achievements with locked/unlocked status |
| `/api/achievements/user` | GET | Current user's unlocked achievements |
| `/profile` | GET | Render profile page |
| `/api/profile` | GET | JSON: user info, level, XP, streaks, icons, themes |
| `/api/profile/icon` | POST | Update icon (validates level/mission unlock) |
| `/api/profile/theme` | POST | Update theme colour (validates level unlock) |

## Template Context

Available in all templates via context processor:
- `current_user` — `User` object or `None`
- `idle_timeout_ms` — idle timeout in milliseconds (default 300000 = 5 min)

## Auth Flow

1. Browser hits any route -> `require_trusted_ip` before_request
2. If no PIN hash configured -> auth bypassed entirely
3. If IP not in `TrustedIP` table (or expired after 7 days) -> redirect to `/pin`
4. PIN entry: max 5 attempts per 15-min window, bcrypt-verified
5. On success: IP added to `TrustedIP`, redirect to `/` (login page)
6. Login page: tap user card -> POST `/session` -> sets `session["current_user_id"]` -> redirect to `/chores-page`
7. Idle timer (Alpine.js in base.html): auto-logout after 5 min inactivity

## CSS Conventions

- **Theme:** Dark background (`#0d1117`), neon accents, glassmorphism
- **Per-user themes:** Set via `body.theme-{color}` class, overrides `--accent` and `--accent-2` CSS vars
- **Available theme colors:** cyan, magenta, purple, lime, gold, red, blue
- **IMPORTANT — Borders on gradient elements:** Never use `border` with semi-transparent colors on elements that have a gradient background. The border blends with the gradient, producing visible colored lines. Use `box-shadow: inset 0 0 0 1px <color>` instead.
- **Cache busting:** Update `?v=X.Y.Z` in templates when changing CSS/JS

## Tech Stack

- **Backend:** Flask, SQLAlchemy, Flask-Migrate, Flask-SocketIO, APScheduler
- **Frontend:** Vanilla JS + Alpine.js (CDN), Sortable.js, canvas-confetti
- **Database:** SQLite (instance/chores.db)
- **Server:** eventlet via `socketio.run()` (use_reloader=False for APScheduler compat)
- **Testing:** pytest, Flask test client, in-memory SQLite per test

## Current Users (Production)

Calvin, Carly, Jamo, Lilah, Travis
