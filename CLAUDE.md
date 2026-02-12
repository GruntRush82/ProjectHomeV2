# Project Home V2 — Development Reference

This file covers the V2 codebase (branch `v2`). For deployment, SSH, and V1 production info, see `~/CLAUDE.md`.

## Quick Start

```bash
# Activate venv and run locally
source venv/bin/activate
python run.py              # Starts on http://0.0.0.0:5000
```

- **Branch:** `v2` (V1 stays live on `master`)
- **Specs:** `specs/V2_PLAN.md` (phased plan + session handoff log), `specs/DECISIONS.md` (92 finalized decisions)
- **Tests:** `pytest tests/` (71 tests, all passing as of Phase 2 completion)
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
│   ├── auth.py              # PIN, IP trust, login, sessions
│   ├── calendar_bp.py       # Calendar dashboard, events CRUD, today API
│   ├── chores.py            # Chore CRUD, grid, archive, reset, streak tracking
│   ├── grocery.py           # Grocery list CRUD, email
│   └── users.py             # User CRUD
├── models/
│   ├── user.py              # User (username, email, allowance, xp, level, icon, theme...)
│   ├── chore.py             # Chore, ChoreHistory
│   ├── calendar.py          # CalendarEvent
│   ├── grocery.py           # GroceryItem
│   └── security.py          # TrustedIP, PinAttempt, AppConfig
├── services/
│   ├── __init__.py
│   └── google_cal.py        # Google Calendar API integration (service account, caching)
├── scripts/
│   └── migrate_v1_data.py   # One-time V1 data migration
├── static/
│   ├── css/style.css        # Dark neon glassmorphic theme
│   ├── js/scripts.js        # Chore/grocery frontend logic
│   └── sounds/cheer.wav
└── templates/
    ├── base.html            # Base layout, bottom nav, Alpine.js idle timer
    ├── calendar.html        # Daily calendar dashboard (served at /calendar)
    ├── login.html           # User selection cards (served at /)
    ├── pin.html             # PIN entry pad (served at /pin)
    └── chore_tracker.html   # Chore grid SPA (served at /chores-page)

run.py                       # Entry point: socketio.run(app)
tests/
├── conftest.py              # Shared fixtures (app, db, client, auth_client, sample_users, etc.)
├── test_smoke.py            # 5 smoke tests
├── unit/
│   └── test_streaks.py      # 4 streak tracking unit tests
└── api/
    ├── test_auth.py         # 10 auth/PIN/IP-trust tests
    ├── test_calendar_api.py # 11 calendar API tests (today, events CRUD)
    ├── test_session.py      # 8 login/logout/session tests
    ├── test_chores_api.py   # Chore CRUD tests
    ├── test_grocery_api.py  # Grocery CRUD tests
    └── test_users_api.py    # User CRUD tests
```

## Database Models

**User:** id, username (unique), email, allowance, is_admin, icon, theme_color, xp, level, streak_current, streak_best

**Chore:** id, description, completed, user_id (FK), day, rotation_type (static/rotating), rotation_order (JSON), base_user_id (FK)

**ChoreHistory:** id, chore_id (FK), username, date, completed, day, rotation_type

**GroceryItem:** id, item_name, added_by, created_at

**CalendarEvent:** id, title, description, event_date, event_time, created_by (FK→User), google_event_id, created_at

**TrustedIP:** id, ip_address (unique), trusted_at, last_seen

**PinAttempt:** id, ip_address, attempted_at, success

**AppConfig:** id, key (unique), value — runtime key/value store with `AppConfig.get(key)` / `AppConfig.set(key, value)`

## Routes

### Auth (auth.py)
| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Login page (user selection cards) |
| `/pin` | GET/POST | PIN entry + validation |
| `/session` | POST | Start session (sets `current_user_id`) |
| `/session/logout` | GET | End session, redirect to `/` |

**App-wide before_request:** `require_trusted_ip` — redirects untrusted IPs to `/pin`. Skips `/static`, `/pin`, `/favicon.ico`. Bypassed entirely if no PIN hash is configured.

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

### Users (users.py)
| Route | Method | Purpose |
|-------|--------|---------|
| `/users` | GET/POST | List all / create user |
| `/users/<id>` | DELETE | Delete user + cascade chores |

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
