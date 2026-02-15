# Project Home V2 — Master Plan

> **Status:** Phase 3 COMPLETE — Bank & Savings fully implemented. 135 tests passing.
>
> **Branch:** `v2` (created from `master`)
>
> **Last updated:** 2026-02-14 (Phase 3 completed)

---

## Current Status

**What's done:**
- V2 requirements finalized across two Q&A rounds (92 decisions)
- `specs/DECISIONS.md` — canonical decisions reference
- `specs/V2_Questions_Round2.md` — Round 2 Q&A with answers
- `v2` branch created from master
- V1 codebase fully reviewed
- Phased plan complete (below)
- **Phase 1 COMPLETE** — project restructured, dark theme, auth/PIN, login screen, all V1 features working, 56 tests passing
- **Phase 2 COMPLETE** — Calendar dashboard, Google Calendar integration, CalendarEvent model, streak tracking, 71 tests passing
- **Phase 3 COMPLETE** — Bank & Savings: 4 models (BankAccount, SavingsDeposit, Transaction, SavingsGoal), 3 services (email, interest, allowance), bank blueprint (9 routes), bank.html with Alpine.js + crystal/gem visualization, nav bar interest ticker, weekly reset integration (allowance deposit, interest credit, IP expiry). 135 tests passing

**What's next:**
- Phase 3 COMPLETE. Begin Phase 4: Missions (multiplication tables, piano practice)
- Phase 3 plan archived at `specs/PHASE3_IMPLEMENTATION_PLAN.md`

---

## Quick Reference

| Item | Location |
|------|----------|
| Decisions log | `specs/DECISIONS.md` (92 items) |
| Round 1 Q&A | `/home/felke/projecthome/specs/V2_Questions_and_Suggestions.md` |
| Round 2 Q&A | `specs/V2_Questions_Round2.md` |
| Original spec | `/home/felke/projecthome/specs/Project Home V2.txt` |
| V1 main app | `Family_Hub1_0.py` (~453 lines, single file) |
| V1 frontend | `static/scripts.js` (~560 lines vanilla JS) |
| V1 production | `master` branch → 68.183.192.133:5000 |
| Existing migrations | `migrations/versions/` (2 files) |
| Current users | Calvin ($15), Carly ($100), Jamo ($0), Lilah ($15), Travis ($100) |
| Config | `reporting_config.yaml` (email + allowance per user — to be migrated into DB) |

---

## V1 Code Assessment

1. **Single-file backend** — `Family_Hub1_0.py` has all 4 models and all routes. Must be split into blueprints.
2. **User model is minimal** — only `id` and `username`. Email/allowance live in `reporting_config.yaml`.
3. **Alembic already set up** — 2 migration files. We continue from here.
4. **reporting.py** — `_send_email()` and Mailgun integration reusable directly.
5. **Frontend is vanilla JS** — no build step. Alpine.js introduced incrementally.
6. **CSS** — light theme with glassmorphism, responsive. V2 is a **complete redesign** (dark, modern, high-contrast).
7. **Sortable.js + confetti** — loaded via CDN, works well. Kept for V2.
8. **Weekly reset logic** — `weekly_archive_task()` handles archiving + rotation. V2 extends it (allowance deposit, interest credit, IP expiry).

---

## Architecture Overview

### App name: **Felker Family Hub**

### Design direction
- **Complete UX redesign** — modern, dark theme with high contrast
- Kids must feel this is a BIG upgrade from V1
- Neon accent colors on dark backgrounds, careful contrast for readability
- Glassmorphic cards, smooth animations, particle effects at higher levels
- iPad landscape-first, responsive to phone via container queries

### File structure
```
project-home/
├── app/
│   ├── __init__.py          # Flask app factory, register blueprints, extensions
│   ├── extensions.py        # db, migrate, socketio, scheduler instances
│   ├── config.py            # Default config values (overridden by AppConfig DB table)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py          # User
│   │   ├── chore.py         # Chore, ChoreHistory
│   │   ├── grocery.py       # GroceryItem
│   │   ├── calendar.py      # CalendarEvent
│   │   ├── bank.py          # BankAccount, SavingsDeposit, Transaction, SavingsGoal
│   │   ├── mission.py       # Mission, MissionAssignment, MissionProgress
│   │   ├── achievement.py   # Achievement, UserAchievement
│   │   └── security.py      # TrustedIP, PinAttempt, AppConfig
│   ├── blueprints/
│   │   ├── auth.py          # PIN verification, IP trust, session management
│   │   ├── users.py         # User CRUD, profile, icon/theme selection
│   │   ├── chores.py        # Chore CRUD, weekly reset, rotation
│   │   ├── grocery.py       # Grocery CRUD, send email
│   │   ├── calendar_bp.py   # Google Calendar sync, local event CRUD
│   │   ├── bank.py          # Cash/savings operations, cashout, interest ticker
│   │   ├── missions.py      # Mission assignment, training, testing, approval
│   │   ├── achievements.py  # Achievement checks, catalog, XP grants
│   │   └── admin.py         # Admin dashboard, config management, data export
│   ├── services/
│   │   ├── email.py         # Mailgun helper (from reporting.py)
│   │   ├── google_cal.py    # Google Calendar API wrapper (read + write + delete)
│   │   ├── interest.py      # Interest calculation logic
│   │   ├── allowance.py     # Allowance tier calculation (from reporting.py)
│   │   ├── xp.py            # XP grant + level-up logic
│   │   └── weekly_reset.py  # Weekly job: archive, rotate, deposit, interest, expire IPs
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css    # Complete redesign: dark, modern, high-contrast
│   │   ├── js/
│   │   │   ├── app.js       # Alpine.js global state, nav, session timeout, interest ticker
│   │   │   ├── calendar.js  # Calendar page logic
│   │   │   ├── chores.js    # Chore page (evolved from V1 scripts.js)
│   │   │   ├── grocery.js   # Grocery page
│   │   │   ├── bank.js      # Bank page + SocketIO full ticker
│   │   │   ├── missions.js  # Mission training/testing UI
│   │   │   └── profile.js   # User page / achievements / icons
│   │   ├── sounds/
│   │   │   ├── cheer.wav
│   │   │   ├── cha-ching.wav
│   │   │   ├── level-up.wav
│   │   │   ├── achievement.wav
│   │   │   └── fireworks.wav
│   │   └── icons/           # SVG/CSS icon definitions for profile icons
│   └── templates/
│       ├── base.html        # Layout: bottom nav (with interest ticker), Alpine.js, SocketIO
│       ├── login.html       # User selection (icons + levels visible)
│       ├── pin.html         # PIN entry (untrusted IP)
│       ├── calendar.html    # Daily dashboard (separated Events + Chores)
│       ├── chores.html      # Chore grid (user-filtered, V1-style layout)
│       ├── grocery.html     # Shared grocery list
│       ├── bank.html        # Bank page (overview + savings) with History tab
│       ├── missions.html    # Mission hub
│       ├── profile.html     # User page / achievements / icon picker / theme
│       └── admin.html       # Admin dashboard
├── migrations/
├── specs/
├── run.py                   # Entry point
├── Dockerfile
├── requirements.txt
└── .env
```

### Key tech choices
- **Alpine.js** via CDN (no build step) — nav state, forms, idle timeout, interest ticker display
- **Flask-SocketIO** — real-time interest push for bank page + nav bar ticker
- **Flask Blueprints** — one per feature area
- **AppConfig DB table** — all config values editable via admin UI, with `config.py` defaults as fallback

### Icon system (three tiers)
1. **Starter icons (20)** — plain, clean, available from start. Question mark is default.
2. **Level-unlocked icons** — progressively flashier at higher levels. Cooler borders, glow effects, subtle animations. Visible on login screen.
3. **Mission icons** — unique per mission, ultra-flashy. Animated glow/pulse, gold/diamond borders, particle effects on hover. The most visually impressive icons in the app.

---

## Phased Plan

---

### Phase 1: Foundation, Security & Login

**Goal:** Restructure the app, add security, create the user selection experience, and redesign the UI. At the end of this phase: new dark modern UX, PIN-gated access, user login screen with levels, bottom nav bar with interest ticker placeholder, and all V1 functionality (chores + grocery) working.

#### 1.1 Project restructure
- Create `app/` package with factory pattern (`create_app()`)
- Create `extensions.py` (db, migrate, socketio, scheduler)
- Create `run.py` as new entry point
- Create `requirements.txt`
- Update `Dockerfile`
- Add Alpine.js via CDN to `base.html`

#### 1.2 Complete UX redesign
- **New `style.css`** — dark theme, modern, high contrast
  - Dark background (#0d1117 or similar), with neon accent colors
  - Glassmorphic cards with subtle borders and shadows
  - Large touch targets (minimum 44px) for iPad
  - Poppins font retained, adjusted weights for dark backgrounds
  - CSS custom properties for per-user accent colors
  - Container queries for phone responsiveness
  - Smooth transitions and micro-animations throughout
- **`base.html`** — persistent bottom nav bar:
  - Icons: Calendar, Chores, Grocery, Bank, Missions, Profile
  - Current user avatar + name + level badge
  - Interest ticker slot (shows $0.000000 until bank is built in Phase 3)
  - "Switch User" button
- Brand: "Felker Family Hub" displayed on login screen

#### 1.3 Database changes

**Modify `User` model — add columns:**
```
email           String(200), nullable
allowance       Float, default=0
is_admin        Boolean, default=False
icon            String(50), default='question_mark'
theme_color     String(20), default='cyan'
xp              Integer, default=0
level           Integer, default=1
streak_current  Integer, default=0
streak_best     Integer, default=0
```

**New table: `TrustedIP`**
```
id              Integer, PK
ip_address      String(45), unique, not null
trusted_at      DateTime, not null
last_seen       DateTime, not null
```

**New table: `PinAttempt`**
```
id              Integer, PK
ip_address      String(45), not null
attempted_at    DateTime, not null
success         Boolean, not null
```

**New table: `AppConfig`**
```
id              Integer, PK
key             String(100), unique, not null
value           Text, not null
```

**Seeded AppConfig values:**
```
pin_hash            <bcrypt hash of default 4-digit PIN>
idle_timeout_min    5
interest_rate       0.05
savings_max         100.00
savings_lock_days   30
cashout_min         1.00
savings_deposit_min 1.00
```

**Migration:** Alembic migration adds User columns, creates new tables. Data migration script copies `reporting_config.yaml` values into User rows. Sets Travis as admin.

#### 1.4 Security
- `auth` blueprint with before-request hook:
  - Check request IP in TrustedIP table (not expired) → allow
  - Otherwise → redirect to `/pin`
  - Exempt: `/pin`, `/static/*`
- `GET /pin` — PIN entry page (styled to match new dark theme)
- `POST /pin` — validate PIN against AppConfig `pin_hash`
  - Rate limit: 5 attempts → 15-min lockout (exponential backoff)
  - On success: add IP to TrustedIP, redirect to `/`
- Session: Flask session stores `current_user_id`
- Frontend idle timer (Alpine.js): 5 minutes no interaction → immediate snap back to login
- `visibilitychange`: on tab hidden >5 min → snap back on return

#### 1.5 User selection screen (login)
- `GET /` → `login.html`
- Grid of user cards, ordered by creation date
- Each card shows: profile icon + username + **level badge**
  - Level 1 = basic card
  - Higher levels = progressively cooler card effects (glow, border animation) — even from Phase 1
- Tap user → `POST /session` → set session → redirect to `/calendar`
- Switch user → `POST /session/logout` → back to `/`

#### 1.6 Migrate V1 into blueprints
- Chore routes → `chores` blueprint
  - Pre-filtered to current user
  - Full 7-day grid (V1 layout, new UX)
  - Admin can toggle to see all users
- Grocery routes → `grocery` blueprint (unchanged, shared)
- User routes → `users` blueprint
- Weekly reset continues via scheduler
- Confetti + cheer sound carried over

#### 1.7 Data migration script
- `reporting_config.yaml` → User.email, User.allowance
- Set Travis `is_admin=True`
- Run once on first V2 deploy

**Deliverable:** Completely redesigned dark modern app. PIN-gated. Login screen with user levels. Bottom nav. Chores + grocery working. Ready for calendar.

---

### Phase 2: Calendar Dashboard & Streaks

**Goal:** Build the daily calendar page (the new home screen). Google Calendar integration, chore check-off from calendar, streak tracking.

#### 2.1 Google Calendar integration
- `services/google_cal.py`:
  - Service account client using JSON key from `.env`
  - `get_todays_events(calendar_id)` → list of `{title, start_time, end_time, description, google_event_id}`
  - `create_event(calendar_id, title, date, time, description)` → push to Google, return event ID
  - `delete_event(calendar_id, google_event_id)` → delete from Google
  - In-memory cache with 15-minute TTL

#### 2.2 Database changes

**New table: `CalendarEvent`**
```
id                Integer, PK
title             String(200), not null
description       Text, nullable
event_date        Date, not null
event_time        Time, nullable
created_by        Integer, FK(user.id), not null
google_event_id   String(200), nullable
created_at        DateTime, not null
```

#### 2.3 Calendar blueprint
- `GET /calendar` → `calendar.html` — daily dashboard:
  - Today's date displayed prominently
  - **Events section:** Google Calendar events sorted chronologically by time
  - **Chores section:** User's chores for today (from Chore model, day filter)
  - **Streak counter:** "🔥 5-week streak" (or similar, matching dark theme)
  - Chore check-off buttons (reuse `PUT /chores/<id>`)
  - Confetti + cheer on completion
- `POST /calendar/events` — create event:
  - Simple form: title, date, time (optional)
  - Save to CalendarEvent table
  - Push to Google Calendar API
- `DELETE /calendar/events/<id>` — delete event:
  - Delete from CalendarEvent table
  - Delete from Google Calendar if `google_event_id` exists
- `GET /api/calendar/today` — JSON endpoint for today's merged data

#### 2.4 Streak tracking
- On weekly reset, for each user:
  - If 100% chore completion → increment `streak_current`, update `streak_best` if new record
  - If <100% → reset `streak_current` to 0
- Streak displayed on calendar page
- Streak data feeds into achievements (Phase 5)

**Deliverable:** After login, user lands on a clean daily dashboard. Google Calendar events in one section, today's chores in another. Check off chores, see streak. Create/delete calendar events that sync with Google.

---

### Phase 3: Bank & Allowance System

**Goal:** Replace email-based allowance with an in-app bank. Cash account, savings with per-deposit locks, real-time interest ticker in nav bar, cashout flow, transaction history. The most exciting feature for the kids.

#### 3.1 Database changes

**New table: `BankAccount`**
```
id                      Integer, PK
user_id                 Integer, FK(user.id), unique, not null
cash_balance            Float, default=0, not null
total_cashed_out        Float, default=0, not null
total_interest_earned   Float, default=0, not null
last_interest_credit    DateTime, not null
created_at              DateTime, not null
```

**New table: `SavingsDeposit`**
```
id                Integer, PK
user_id           Integer, FK(user.id), not null
amount            Float, not null
deposited_at      DateTime, not null
lock_until        DateTime, not null
interest_rate     Float, not null          # snapshot rate at deposit time
withdrawn         Boolean, default=False
withdrawn_at      DateTime, nullable
```

**New table: `Transaction`**
```
id                Integer, PK
user_id           Integer, FK(user.id), not null
type              String(30), not null     # 'allowance', 'cashout', 'savings_deposit',
                                           # 'savings_withdrawal', 'interest', 'mission_reward'
amount            Float, not null          # positive = in, negative = out
balance_after     Float, not null          # cash balance after this transaction
description       String(300), nullable
created_at        DateTime, not null
```

**New table: `SavingsGoal`**
```
id                Integer, PK
user_id           Integer, FK(user.id), not null
name              String(200), not null
target_amount     Float, not null
created_at        DateTime, not null
completed_at      DateTime, nullable
```

#### 3.2 Bank blueprint — endpoints

- `GET /bank` → `bank.html`
- `POST /bank/cashout` — cash out
- `POST /bank/savings/deposit` — move cash to savings
- `POST /bank/savings/withdraw/<deposit_id>` — withdraw unlocked deposit (direct cashout)
- `POST /bank/savings/goal` — create/update savings goal
- `GET /bank/transactions` — paginated transaction history (History tab)
- `GET /bank/stats` — historical stats JSON
- `GET /api/bank/ticker` — interest ticker data for nav bar (SocketIO also available)

#### 3.3 Bank page layout

**Main page (single scrollable view):**
- **Cashout section (top, prominent):**
  - Large display: "Available to cash out: $XX.XX"
  - This total = cash_balance + sum of unlocked (non-withdrawn) savings deposits
  - "Cash Out" button with confirmation modal
  - Note: cash is drawn first, then unlocked savings
- **Cash account:** Current cash balance
- **Savings account:**
  - Total savings balance with real-time interest ticker (6 decimals, ticking)
  - Yearly interest projection at current balance
  - "Deposit to Savings" button (with amount input)
- **Savings deposits visualization:**
  - Each deposit shown as a **glowing crystal/gem** in a stacked display
  - Locked deposits: encased in a translucent frost/ice layer with countdown timer
  - Unlocked deposits: ice cracked away, gem pulses with warm glow, "Withdraw" available
  - Amount and deposit date on each gem
  - Visual progression: small deposits = small gems, larger = bigger gems
  - Animation: when a deposit unlocks, the ice cracks and shatters (with sound)
- **Savings goal:** Progress bar toward goal if set
- **Weekly report:** Last week's chore completion, missed chores, allowance earned
- **Stats:** Total cashed out, total interest earned

**History tab:**
- Transaction ledger — scrollable list of all transactions
- Type, amount, description, date for each

#### 3.4 Interest system

**How interest works:**
- Interest accrues on ALL savings deposits (locked AND unlocked) until withdrawn
- Rate is weekly (e.g., 5% of $100 = $5/week)
- Interest is paid into the **cash account** (not back into savings — no compounding)
- Savings has a configurable maximum balance

**Server-side (authoritative):**
- On weekly reset: calculate exact interest since last credit
  - `total_active_savings * weekly_rate`
  - Credit to cash_balance
  - Record transaction (type='interest')
  - Update `total_interest_earned`
  - Update `last_interest_credit` timestamp

**Client-side (visual ticker):**
- On page load, server sends: `total_active_savings`, `weekly_rate`, `last_interest_credit` timestamp
- Alpine.js calculates: `savings * rate / (7*24*60*60) * elapsed_seconds_since_last_credit`
- Displays with 6 decimal places, updates via `requestAnimationFrame`
- Syncs with server every 30 seconds to prevent drift

**Nav bar ticker:**
- Small format in bottom nav: "+$0.000042" ticking up
- Shows interest accumulated since last weekly credit
- Powered by same Alpine.js calculation (no extra SocketIO needed for nav bar)
- Full SocketIO used on bank page for richer real-time updates

#### 3.5 Cashout flow

1. User taps "Cash Out" button
2. Confirmation modal shows: total amount (cash + unlocked savings), breakdown
3. On confirm:
   - Cash balance → $0
   - All unlocked savings deposits marked as withdrawn
   - `total_cashed_out` incremented
   - Transaction recorded
   - Mailgun email sent to user's email address
4. Celebration animation + cha-ching sound
5. Email format:
```
Subject: Felker Family Hub - Cash Out Confirmation

Hi [name],

You've cashed out $[amount] on [date] at [time].

Show this email to collect your payout!

— Felker Family Hub
```

#### 3.6 Weekly reset integration
Extend `weekly_reset.py`:
1. Archive chores + rotate (existing)
2. Calculate each user's completion % (existing)
3. Calculate allowance per tier rules (existing)
4. **Deposit allowance into cash_balance**
5. **Record allowance transaction**
6. **Calculate and credit interest earned**
7. **Record interest transaction**
8. **Expire trusted IPs older than 7 days**
9. **Send weekly digest email to admin users**
10. **Store weekly performance snapshot** (for bank page weekly report)

**Deliverable:** Kids see money growing in real time in the nav bar everywhere they go. Bank page has cash, savings crystals with lock timers, cashout flow, transaction history. Parents get weekly digest.

---

### Phase 4: Missions

**Goal:** Build the mission framework and two missions (multiplication, piano). Missions reward cash + unique ultra-flashy profile icons. Admin-assigned, state-machine-driven.

#### 4.1 Database changes

**New table: `Mission`**
```
id                Integer, PK
title             String(200), not null
description       Text, not null
mission_type      String(50), not null       # 'multiplication', 'piano', etc.
config            JSON, not null             # type-specific config
reward_cash       Float, default=0
reward_icon       String(50), not null       # unique icon ID for this mission
created_at        DateTime, not null
```

**New table: `MissionAssignment`**
```
id                Integer, PK
mission_id        Integer, FK(mission.id), not null
user_id           Integer, FK(user.id), not null
state             String(20), not null, default='assigned'
                  # 'assigned','training','ready_for_test','testing',
                  # 'completed','failed','pending_approval'
assigned_at       DateTime, not null
started_at        DateTime, nullable
completed_at      DateTime, nullable
```

**New table: `MissionProgress`**
```
id                Integer, PK
assignment_id     Integer, FK(mission_assignment.id), not null
session_type      String(20), not null       # 'training', 'test'
data              JSON, not null
score             Integer, nullable
duration_seconds  Integer, nullable
created_at        DateTime, not null
```

#### 4.2 Mission state machine

```
assigned ──→ training ──→ training (repeat) ──→ ready_for_test ──→ testing
                                                                      │
                                                          ┌───────────┤
                                                          ▼           ▼
                                                       failed    completed
                                                          │           │
                                                          ▼           ▼
                                                       training    reward!
```

For piano (admin-verified): `testing → pending_approval → completed`

Each mission type implements:
- `get_training_session(assignment)` → training content
- `evaluate_training(assignment, results)` → update progress, check readiness
- `get_test(assignment)` → test content
- `evaluate_test(assignment, results)` → pass/fail

#### 4.3 Multiplication mission

**Config:**
```json
{
  "range_min": 1,
  "range_max": 12,
  "test_correct_required": 35,
  "test_time_seconds": 60,
  "readiness_threshold": 0.85
}
```

**Training:**
- User chooses session length: 10, 20, or 30 problems
- Random problems from 1-12 x 1-12
- Track each answer: question, user_answer, correct_answer, time_taken
- Store wrong-answer frequency in MissionProgress.data
- Weight future questions toward weak facts
- After session: show score, which facts need work

**Readiness:**
- Rolling accuracy >= 85% across last 3 sessions → `ready_for_test`
- Notification: "You're ready for the test!"

**Test:**
- 60-second timer, random facts
- Must get 35 correct in 60 seconds
- Pass → `completed`
- Fail → encouraging message, score shown, back to `training`

**Reward icon:** Lightning brain — animated electric pulse, gold border, particle sparks on hover

#### 4.4 Piano mission

**Config:**
```json
{
  "piece_name": "Fur Elise",
  "description": "Play Fur Elise all the way through without mistakes",
  "verification": "admin_approval"
}
```

**Flow:**
- `assigned` → `training` (user clicks "Start Practicing")
- `training` → `testing` (user clicks "I'm ready to perform")
- `testing` → `pending_approval` (user clicks "I played it")
- `pending_approval` → `completed` (admin approves on admin dashboard)
- Admin can reject → back to `training` with optional message

**Reward icon:** Golden music note — animated glow/pulse, diamond border, trailing sparkle particles on hover

#### 4.5 Mission completion celebration
When a mission is completed:
1. **Full-screen takeover:** dark overlay, mission icon displayed LARGE center-screen
2. **Fireworks animation** — canvas-based, fills the screen for ~5 seconds
3. **Cheering sound effect** — triumphant fanfare
4. **Cash reward notification** — "$XX.XX added to your cash account!"
5. **Icon display** — the unique mission icon stays center-screen, slowly rotating with particle effects, for ~60 seconds
6. **Auto-equip** — mission icon becomes the user's active profile icon

#### 4.6 Missions blueprint
- `GET /missions` → mission hub (active + completed missions)
- `POST /missions/<assignment_id>/start` — begin training
- `GET /missions/<assignment_id>/train` — get training session
- `POST /missions/<assignment_id>/train` — submit training results
- `GET /missions/<assignment_id>/test` — get test
- `POST /missions/<assignment_id>/test` — submit test results
- **Admin:**
  - `GET /admin/missions` — all missions + assignments
  - `POST /admin/missions` — create mission definition
  - `POST /admin/missions/<id>/assign/<user_id>` — assign to user
  - `POST /admin/missions/<assignment_id>/approve` — approve pending mission
  - `POST /admin/missions/<assignment_id>/reject` — reject, back to training

**Deliverable:** Two working missions with adaptive training, state machine, admin approval for piano, and spectacular completion celebrations with unique icons.

---

### Phase 5: Achievements, XP & Gamification

**Goal:** XP system, leveling with increasing difficulty, achievement catalog (XP rewards only — no icon unlocks), level-unlocked icons, tiered notifications, per-user themes. The fun layer.

#### 5.1 Database changes

**New table: `Achievement`**
```
id                  Integer, PK
name                String(200), not null
description         String(500), not null
icon                String(50), not null         # display icon for the achievement itself
category            String(50), not null         # 'chores', 'bank', 'streaks'
requirement_type    String(50), not null         # 'streak_weeks', 'savings_max', etc.
requirement_value   String(200), not null        # threshold value
xp_reward           Integer, not null
tier                String(10), not null         # 'bronze', 'silver', 'gold'
is_visible          Boolean, default=True
display_order       Integer, default=0
```

**New table: `UserAchievement`**
```
id                  Integer, PK
user_id             Integer, FK(user.id), not null
achievement_id      Integer, FK(achievement.id), not null
unlocked_at         DateTime, not null
```

#### 5.2 XP & leveling

**XP sources:**
| Source | XP |
|--------|----|
| Complete a chore | +10 |
| 100% weekly completion | 2x all chore XP for the week |
| Streak milestones (7/14/30/60/90 days) | via achievements |
| Mission completed | +500 |
| Achievement unlocked | varies (see catalog) |
| Savings goal reached | via achievement |

**Level thresholds (increasingly difficult):**

| Level | Total XP | XP to reach | Name |
|-------|----------|-------------|------|
| 1 | 0 | — | Rookie |
| 2 | 100 | 100 | Apprentice |
| 3 | 250 | 150 | Helper |
| 4 | 500 | 250 | Star |
| 5 | 850 | 350 | Champion |
| 6 | 1,300 | 450 | Hero |
| 7 | 1,900 | 600 | Legend |
| 8 | 2,700 | 800 | Master |
| 9 | 3,700 | 1,000 | Titan |
| 10 | 5,000 | 1,300 | Ultimate |

*At ~300 XP/week with perfect chores, Level 10 takes ~17 weeks (~4 months). Achievable but requires sustained effort.*

**Level-up effects:**
- **Level-up celebration:** fanfare sound, full-screen particle burst, level badge animation
- **Login screen impact:** higher levels = cooler card effects (glow, animated border, particles)
- **App-wide impact (progressive):**
  - Level 1-3: Clean, standard dark theme
  - Level 4-5: Subtle ambient particle effects in background
  - Level 6-7: Enhanced glow effects on interactive elements
  - Level 8-9: Premium animated accents, richer particle system
  - Level 10: Full animated theme with ambient effects throughout

**Level-unlocked icons:**

| Level | Icons unlocked |
|-------|---------------|
| 1 | 20 plain starter icons |
| 3 | 2 enhanced icons (colored borders) |
| 5 | 2 glowing icons (animated border pulse) |
| 7 | 2 premium icons (glow + particle trail) |
| 10 | 2 ultimate icons (full animation + effects) |

#### 5.3 Achievement catalog (XP rewards only)

| Achievement | Category | Requirement | Tier | XP |
|---|---|---|---|---|
| First Steps | chores | Complete first chore | bronze | 25 |
| Week Warrior | chores | 100% chores for 1 week | silver | 100 |
| Chore Machine | chores | 100% chores for 4 weeks (cumulative) | gold | 250 |
| Streak Starter | streaks | 7-day streak | bronze | 50 |
| On Fire | streaks | 14-day streak | silver | 100 |
| Unstoppable | streaks | 30-day streak | gold | 500 |
| Legendary | streaks | 60-day streak | gold | 750 |
| Immortal | streaks | 90-day streak | gold | 1,000 |
| Penny Saver | bank | First savings deposit | bronze | 25 |
| Savings Pro | bank | Max out savings account | silver | 200 |
| First Cashout | bank | Cash out for the first time | bronze | 25 |
| Big Spender | bank | Total cashed out >= $100 | silver | 100 |
| Interest Earner | bank | Total interest earned >= $10 | silver | 100 |
| Goal Getter | bank | Complete a savings goal | silver | 200 |

*No mission-related achievements. Missions have their own reward system.*

#### 5.4 Tiered achievement notifications

| Tier | Notification style |
|------|-------------------|
| Bronze | Small toast in corner (3 seconds) + subtle ding sound |
| Silver | Banner slides down from top (5 seconds) + achievement sound |
| Gold | Full-screen celebration: dark overlay, achievement card center-screen, particle effects, triumphant sound (8 seconds) |

#### 5.5 Per-user themes
- Accent color options: cyan, magenta, purple, lime, gold, red, blue
- Some colors unlockable at certain levels (gold at level 5, etc.)
- When user logs in, CSS custom properties update to their chosen color
- Affects: nav bar accent, progress bars, button gradients, name color, card borders

#### 5.6 Achievements blueprint
- `GET /achievements` → achievement catalog (all achievements, locked/unlocked)
- `GET /api/achievements/<user_id>` → JSON achievement status
- Achievement check service: called after chore completion, cashout, weekly reset, mission complete, etc.

#### 5.7 User profile page
- `GET /profile` → `profile.html`:
  - Large avatar, name, level badge, XP bar to next level
  - Streak counter
  - Achievement showcase: recent unlocks + total count + "View All" to catalog
  - Icon selector: starter icons + level-unlocked + mission-earned (with clear tiers)
  - Theme color picker
  - Settings: name, email

**Deliverable:** Full gamification. Kids earn XP, level up with increasing difficulty, unlock progressively cooler icons, see tiered achievement notifications, customize their theme. Login screen shows everyone's level with visual effects. App visually evolves as you level up.

---

### Phase 6: Admin Dashboard, Polish & Launch

**Goal:** Admin tools, weekly digest, data export, automated backups, final polish, V1→V2 migration, production deploy.

#### 6.1 Admin dashboard
- `GET /admin` → `admin.html`:
  - **Family overview:** all users at a glance (chore %, bank balance, savings, streak, level, active missions)
  - **Mission management:** create missions, assign to users, approve pending, view progress
  - **User management:** create/delete users, toggle admin flag
  - **Config editor:** ALL values editable in UI — interest rate, savings max, lock period, PIN, idle timeout, cashout min, deposit min
  - **Trusted IPs:** view all, revoke individual IPs
  - **Data export:** CSV/JSON download buttons

#### 6.2 Weekly digest email
One email to all admin users:
```
Subject: Felker Family Hub — Weekly Report

Week of [date]:

CALVIN (Level 4 — Star):
  Chores: 14/16 (88%) → Half allowance: $7.50
  Streak: 3 weeks
  Bank: $42.50 cash, $80.00 savings
  Missions: Multiplication (training — 72% accuracy)
  XP earned this week: 140

LILAH (Level 5 — Champion):
  Chores: 16/16 (100%) → Full allowance: $15.00
  Streak: 5 weeks
  Bank: $15.00 cash, $100.00 savings (maxed!)
  Missions: Multiplication (completed!)
  XP earned this week: 820

[... all kids ...]

— Felker Family Hub
```

#### 6.3 Data export
- `GET /admin/export/transactions?format=csv`
- `GET /admin/export/chore-history?format=csv`
- `GET /admin/export/all?format=json`

#### 6.4 Automated database backup
- Cron job on droplet: daily SQLite backup
- Copy `chores.db` to `/projecthome/backups/chores_YYYY-MM-DD.db`
- Keep last 30 days of backups, auto-delete older
- Simple shell script added to deployment setup

#### 6.5 V1 → V2 migration script
- Copy User data (add new fields with defaults)
- Copy all Chores and ChoreHistory
- Copy GroceryItems
- Migrate `reporting_config.yaml` → User model (email, allowance)
- Initialize BankAccount for all users ($0 starting balance)
- Set Travis as admin
- Test on copy of production DB before cutover

#### 6.6 UX polish
- Touch target audit for iPad
- Loading states / skeleton screens
- Error handling with user-friendly messages
- Animation consistency across pages
- Performance: lazy loading, caching
- Accessibility: focus management, screen reader labels

#### 6.7 Deployment
- Update Dockerfile for V2 dependencies
- Update `.env` with new variables
- Set up backup cron job
- Update CLAUDE.md deployment instructions
- Deploy: merge `v2` → `master`, push, pull on droplet, rebuild container, run migration

**Deliverable:** Complete V2 deployed and live. Admin tools, backups, data export all working. V1 data migrated. Production-ready.

---

## Risks & Tradeoffs

| Risk | Impact | Mitigation |
|------|--------|------------|
| **IP trust is coarse** | Anyone on same network is trusted | Acceptable for family app. PIN gate + weekly expiry. |
| **SQLite concurrency** | SocketIO + multiple users could cause locks | WAL mode. Only 5 users — SQLite handles this fine. |
| **Google Calendar API quota** | Free tier could hit limits with aggressive polling | 15-minute cache. Fetch only on page load. |
| **Interest ticker drift** | Client-side display could diverge from server | 30-second sync. Server authoritative on weekly credit. |
| **Savings visualization complexity** | Per-deposit crystals with animations | Progressive enhancement: basic stacked bars first, add crystal/gem effects iteratively. |
| **No admin security** | Kids could tap Dad's icon and access admin | Accepted risk per owner decision. Monitor for abuse. |
| **Dark theme contrast** | V1 had visibility issues in dark mode | Test extensively. Use WCAG AA contrast ratios. Light text on dark bg. |
| **Single droplet** | No redundancy | Daily automated backups. Acceptable for family app. |

---

## Session Handoff Log

> Each working session should add an entry here before ending.

| Date | Summary | Next Steps |
|------|---------|------------|
| 2026-02-09 | Created v2 branch, DECISIONS.md, V2_PLAN.md, updated CLAUDE.md. | Draft phased plan. |
| 2026-02-09 | V1 codebase reviewed. Initial phased plan drafted. | Round 2 Q&A. |
| 2026-02-09 | Round 2 Q&A completed (30 questions). Plan reformulated: renamed to "Felker Family Hub", complete UX redesign (dark modern theme), mission icons separated from achievements, interest ticker in nav bar, savings crystal visualization, tiered notifications, level-unlocked icons, cashout = cash + unlocked savings, admin approval for piano. DECISIONS.md updated to 92 items. | Owner approval, then begin Phase 1. |
| 2026-02-09 | Testing infrastructure set up. Created TESTING_PLAN.md, requirements.txt, requirements-dev.txt, pyproject.toml, tests/ directory with conftest.py, fixtures, and E2E config. Installed pytest, playwright (Chromium), factory-boy, freezegun, coverage, ruff. All 5 smoke tests pass. Updated .gitignore. | Owner approves plan, then begin Phase 1 implementation. |
| 2026-02-10 | Phase 1 partially implemented (interrupted): 1.1 project restructure (app factory, extensions, config, run.py, requirements), 1.3 DB changes (User expanded, TrustedIP/PinAttempt/AppConfig models, Alembic migration), 1.6 V1 blueprints (chores/grocery/users migrated, 37 tests). | Complete remaining Phase 1: 1.2, 1.4, 1.5, 1.7. |
| 2026-02-11 | Phase 1 COMPLETE. All sub-tasks done: 1.2 dark theme + base.html with bottom nav + Alpine.js; 1.4 auth blueprint (PIN, IP trust, rate limiting, lockout); 1.5 login screen with user cards + level badges + session mgmt; 1.7 data migration script. Chore tracker template extends base.html. 56 tests all passing (auth, session, chores, grocery, users, smoke). | Begin Phase 2: Calendar Dashboard & Streaks. |
| 2026-02-11 | Phase 1 polish: fixed gradient border artifacts on avatars/buttons (replaced semi-transparent `border` with `box-shadow: inset`), added CSS convention note, created V2-specific CLAUDE.md. | Begin Phase 2. |
| 2026-02-11 | Phase 2 COMPLETE. All sub-tasks done: 2.1 Google Calendar service (`app/services/google_cal.py`) with in-memory cache, graceful degradation; 2.2 CalendarEvent model; 2.3 Calendar blueprint + daily dashboard template with Alpine.js (chore check-off, events CRUD, confetti, progress bar); 2.4 Streak tracking in weekly reset (`_update_streaks()`). Post-login redirect changed from chores to calendar. Updated `.env` with Mailgun + Google Calendar config. 71 tests all passing (15 new: 11 calendar API + 4 streak unit tests). | Set `GOOGLE_CALENDAR_ID` in `.env`, share calendar with service account email. Begin Phase 3: Bank & Savings. |
| 2026-02-12 | Phase 2 polish: added `python-dotenv` loading in `run.py` (`.env` wasn't being read), Google Calendar now connected and pulling live events from `carlyfelker@gmail.com`. Confetti changed to fire only on full daily completion (not each chore). Updated CLAUDE.md with `.env` docs and Google Calendar setup notes. | Begin Phase 3: Bank & Savings. |
| 2026-02-14 | Phase 3 sub-phase 3A COMPLETE: Created `app/models/bank.py` (BankAccount, SavingsDeposit, Transaction, SavingsGoal), registered in `models/__init__.py`, Alembic migration `62035d498409` applied. Created `specs/PHASE3_IMPLEMENTATION_PLAN.md` with full Phase 3 plan. 71 tests still passing. | Continue Phase 3: sub-phases 3B–3E. |
| 2026-02-14 | **Phase 3 COMPLETE (3B–3E).** 3B: services (email.py, allowance.py, interest.py) + 21 unit tests (92 total). 3C: bank blueprint (9 routes, cashout, savings, goals, transactions, stats) + 37 API tests (129 total). 3D: bank.html template (Alpine.js, crystal/gem CSS visualization, cashout modal, transaction ledger), nav bar ticker wired in base.html. 3E: weekly reset integration (_process_allowance_and_interest, _expire_trusted_ips) + 6 reset tests. **135 tests all passing.** | Begin Phase 4: Missions. |
