# Project Home V2 — Decisions Log

> Extracted from Q&A sessions (Round 1 + Round 2). This is the canonical reference for all decided requirements.
> If a decision needs to change, update it here and note the date.
> Last updated: 2026-02-09

---

## Branding & Visual Design

| # | Decision | Detail |
|---|----------|--------|
| 1 | **App name: "Felker Family Hub"** | Shown on login screen and nav bar. |
| 2 | **Complete UX redesign** | Modern feel. Dark theme with high contrast (V1 dark mode had visibility issues — avoid that). Kids should feel this is a BIG upgrade. |
| 3 | **iPad landscape-first** | Large touch targets, high contrast. CSS container queries for phone support. |

## Security & Access

| # | Decision | Detail |
|---|----------|--------|
| 4 | **IP-based trust only** | No device tokens or cookies. New IPs require a shared family PIN. |
| 5 | **4-digit shared PIN** | Editable via admin UI. |
| 6 | **Trusted IPs expire on weekly reset** | Same reset that rotates chores and pays allowance. |
| 7 | **PIN lockout** | 5 failed attempts → 15-minute cooldown. Exponential backoff: first 3 immediate, next 3 with 30s delay, after 10 → 15-min lockout. Log all attempts. |
| 8 | **NAT/shared IP is fine** | All devices behind the same router share trust. |
| 9 | **Accessible from anywhere** | Not home-only. New locations just require PIN once per week. |
| 10 | **TrustedIP DB table** | Columns: `ip_address`, `trusted_at`, `last_seen`. Admin can view/revoke. |

## Admin Role

| # | Decision | Detail |
|---|----------|--------|
| 11 | **Admin user exists** | At least one user (e.g., "Dad") flagged as admin. |
| 12 | **No extra security for admin** | Tapping admin user's icon grants admin access. No separate PIN. |
| 13 | **Admin-only actions** | User creation/deletion, mission assignment, mission approval (piano), all config editing. |
| 14 | **Admin dashboard** | View all users' stats, assign missions, manage IPs, edit ALL config values in UI (interest rate, savings max, lock period, PIN, idle timeout, etc.). |

## Login & User Selection

| # | Decision | Detail |
|---|----------|--------|
| 15 | **5-minute idle timeout** | Snaps back to login screen immediately (no countdown). |
| 16 | **Idle triggers** | No interaction for 5 min, browser refresh, device sleep/wake (if feasible). |
| 17 | **Free login for all users** | Tap icon and go. No per-user PIN. |
| 18 | **Easy user switching** | Switch-user button in bottom nav bar, always visible. |
| 19 | **User order on login screen** | Order of creation (not alphabetical, not last-used). |
| 20 | **Level visible on login screen** | Each user's level shown with their icon. Higher levels have cooler effects visible on the login page. |
| 21 | **User data is private** | No cross-user visibility for chores, bank, achievements, or mission progress. Grocery is shared. |

## Icons & Unlockables

| # | Decision | Detail |
|---|----------|--------|
| 22 | **Default icon: question mark** | Everyone starts with a question mark. |
| 23 | **20 plain starter icons** | Available to all from the start. Simple, clean style. |
| 24 | **Level-unlocked icons** | Higher levels unlock progressively flashier icons. More difficult to reach = more flashy. |
| 25 | **Mission-unlocked icons** | Each mission grants a unique, ultra-flashy icon. Animated glow/pulse, gold/diamond border, particle effects on hover. Completely unique per mission (e.g., multiplication = lightning brain, piano = golden music note). |
| 26 | **Achievements do NOT unlock icons** | Achievements grant XP only. Icons come from levels or missions. |
| 27 | **Mission icon auto-equip** | On mission completion, icon displayed largely for ~1 minute center-screen with fireworks, cheering, full fanfare. Then auto-set as profile icon. |

## Calendar & Events

| # | Decision | Detail |
|---|----------|--------|
| 28 | **Google Calendar via service account** | JSON key already obtained. |
| 29 | **Events push to Google Calendar** | Chores do NOT push. Only calendar events. |
| 30 | **Events can be deleted** | Including deletion from Google Calendar. |
| 31 | **One-time events only** | Simple creation form. Recurring events via Google directly. |
| 32 | **Sync frequency** | Implementer's discretion (cache with reasonable refresh). |
| 33 | **Today-only view** | No multi-day view in V2. |
| 34 | **Separated layout** | Events section and Chores section displayed separately (not interleaved). |
| 35 | **Events shown chronologically with times** | Sorted by time within the Events section. |
| 36 | **Chores have no specific time** | Always "sometime today." No time-of-day field. |
| 37 | **Anyone can create events** | No restriction. |

## Chores

| # | Decision | Detail |
|---|----------|--------|
| 38 | **Migrate V1 chores** | Existing chores and chore history migrated into V2. |
| 39 | **Keep rotating chore system** | Static and rotating types both retained. |
| 40 | **Keep allowance tiers** | 100% → full, >=50% → half, <50% → $0. Not proportional. |
| 41 | **Self-managed chore creation** | Users can create/delete their own chores. |
| 42 | **Honor system for completion** | No parent-approval step. Verification in real life. |
| 43 | **Weekly reset stays** | Monday midnight. Rotates chores, resets static, pays allowance, expires IPs. |
| 44 | **Chore page similar to V1** | Full 7-day week grid, new UX, filtered to current user. |

## Bank / Allowance

| # | Decision | Detail |
|---|----------|--------|
| 45 | **Real money** | Cash account = actual money. Cashout triggers email; user shows parent; parent e-transfers. |
| 46 | **Cashout email to user only** | Goes to the user who clicked cashout. |
| 47 | **Cash account floors at $0** | No negative balances. |
| 48 | **Per-deposit lock timers** | Each savings deposit has its own lock period with visual countdown. |
| 49 | **Cashout maximum = cash + unlocked savings + accrued interest** | Cash drawn first, then unlocked savings. "Available to cash out" includes accrued interest (ticks up at penny precision, 2 decimals). |
| 50 | **Cashout confirmation required** | Modal: "You're about to cash out $X. This will send an email. Proceed?" |
| 51 | **Cashout minimum $1.00** | Cannot cash out less than $1. |
| 52 | **Savings deposit minimum $1.00** | Cannot deposit less than $1. |
| 53 | **Savings withdrawal = direct cashout** | Unlocked savings withdrawn goes directly to cashout (email, removed from system). Does not return to cash account. |
| 54 | **Interest on ALL savings** | Interest accrues on both locked AND unlocked deposits. Continues until withdrawn. |
| 55 | **Simple interest only** | Calculated on savings balance, paid into cash account. Not compound. |
| 56 | **Savings max and interest rate in config** | Editable via admin UI. |
| 57 | **Real-time ticking display** | 5-6 decimal places. |
| 58 | **Nav bar ticker shows total available to cash out** | Ticks up at 6-decimal precision (cash + unlocked savings + accrued interest). Bank page "Available to cash out" ticks at penny precision (2 decimals). Bank page savings ticker remains interest-only (6 decimals). |
| 59 | **Bank page layout** | Single page with all sections EXCEPT history on a separate tab. |
| 60 | **Weekly report: last week only** | Shows last week's chore performance + allowance issued. Not scrollable through past weeks. |
| 61 | **Historical stats** | Total cashed out, total interest earned. |
| 62 | **Transaction ledger** | Every deposit, cashout, savings transfer, interest credit logged. On History tab. |
| 63 | **Savings goal feature** | Kids set a goal with progress bar. |
| 64 | **Savings projection** | Show yearly interest at current savings level. |
| 65 | **Savings visualization** | Stacked bars as base, but make it more fun (creative direction TBD — see plan for proposal). |

## Missions

| # | Decision | Detail |
|---|----------|--------|
| 66 | **Admin-assigned only** | Kids cannot self-assign missions. Missions only visible to the assigned user. |
| 67 | **State machine — multiplication** | `assigned` → `training` → `testing` → `completed` (or `failed` → retry immediately). Three test levels: L1 (45 correct, no time limit), L2 (45 correct in 120s), L3 (45 correct in 60s). Only L3 completion unlocks rewards. |
| 68 | **State machine — piano** | `assigned` → `pending_approval` → `completed`. No training or testing phase. Kid clicks "I did it" → admin approves. |
| 69 | **Open-ended, no cooldowns** | No deadlines on missions. No cooldown between test attempts. Unlimited training sessions (no daily cap). |
| 70 | **Multiplication mission** | Range 1–12 x 1–12. Training has two modes: confidence (drills known facts) and explore (teaches new facts). Test requires 45 correct answers; test does NOT end at time limit — completion within the time limit is what's required. |
| 71 | **Multiplication training UX** | iPad-friendly with on-screen numpad. No visible timer or score during training. Wrong answer → encouraging message + second attempt; wrong again → show correct answer + mnemonic device. Memorization-first approach (not deduction). |
| 72 | **Multiplication adaptive weighting** | Gentle bias toward weak facts based on last 3 training sessions. Two training modes: confidence phase (drills mastered facts) and explore phase (introduces/reinforces weak facts). |
| 73 | **Multiplication test levels** | L1: 45 correct, no time limit. L2: 45 correct in 120 seconds. L3: 45 correct in 60 seconds. Each level unlocks the next. Only L3 grants cash reward, XP, and mission profile icon. |
| 74 | **Multiplication test UX** | On-screen numpad input. Timed levels show countdown timer. Encouraging feedback on failure with score shown. No cooldown — can retry immediately. |
| 75 | **Piano mission — simple flow** | Kid enters the piece name. Single "I did it" button flips to `pending_approval`. Admin approves or rejects from admin page. No in-app training or testing. |
| 76 | **Mission rewards** | Admin-defined cash reward per mission + unique ultra-flashy profile icon. Cash auto-deposited to bank account as `mission_reward` transaction. Independent of achievements. |
| 77 | **Mission celebration** | Short celebration (not 60 seconds). Full-screen overlay with fireworks, new profile icon displayed prominently, cash reward amount featured. Dismiss button. Auto-equips icon. |
| 78 | **Multiple active missions** | Users can have multiple missions active simultaneously. Same mission type can be assigned to multiple users independently. |
| 79 | **Mission creation vs assignment** | Mission definitions created in codebase (code/seed). Assignment happens from admin page (minimal admin missions UI needed in Phase 4). Architecture must support adding many new mission types in the future. |
| 80 | **Mission progress is private** | Other users cannot see mission progress. |
| 81 | **Missions are modular** | Pluggable framework. Start with multiplication + piano, add more later. |
| 82 | **Mission training feedback** | End-of-session screen shows score, progress over time, facts mastered count. Motivational tone throughout. |
| 83 | **New mission notification** | When admin assigns a mission, user sees a notification on next login. |
| 84 | **Missions hub empty state** | Shows "No missions assigned yet" message + list of completed missions if any. |

## Gamification & User Page

| # | Decision | Detail |
|---|----------|--------|
| 85 | **XP per chore: 10** | +2x bonus if 100% weekly completion (all chore XP doubled). |
| 86 | **Levels scale increasingly** | e.g., Level 2 = 100 XP, Level 3 = 250 XP, etc. Progressively harder. |
| 87 | **Level-up affects entire app** | Higher levels = visual upgrades across the whole app (particle effects, animated themes), not just profile. |
| 88 | **Per-user themes** | Each user picks an accent color (some unlockable). App feels personalized. |
| 89 | **Achievement catalog** | All achievements shown. Locked ones greyed out with clear requirements. Achievements grant XP only. |
| 90 | **Daily streak tracking** | Consecutive weeks of 100% chore completion. Milestones at 7, 14, 30, 60, 90 days. |
| 91 | **Tiered achievement notifications** | Small achievements = toast. Medium = banner slide-down. Big = full-screen celebration with animation + sound. |
| 92 | **Sound effects and animations** | Level-up fanfare, achievement unlock, cha-ching for deposits, mission fireworks + cheering. |
| 93 | **No competitive/leaderboard elements** | Strictly individual. Shelved for later. |

## Technical Architecture

| # | Decision | Detail |
|---|----------|--------|
| 94 | **Alpine.js** | Lightweight reactive frontend. No build step. |
| 95 | **Flask blueprints** | Split into: `auth`, `calendar`, `chores`, `grocery`, `bank`, `missions`, `users`, `admin`. |
| 96 | **Flask-SocketIO** | Real-time bank ticker (nav bar + bank page) and live notifications. |
| 97 | **Flask-Migrate / Alembic** | Continuing from existing V1 migrations. |
| 98 | **Bottom navigation bar** | Icons for: Calendar, Chores, Grocery, Bank, Missions, Profile. User avatar + interest ticker + switch-user. |
| 99 | **Weekly digest email to parents** | All kids' stats in one email to admin users. |
| 100 | **Data export** | CSV/JSON export for bank transactions and chore history. |
| 101 | **Automated DB backup** | Daily backup of SQLite database on the droplet. |
| 102 | **All config editable in admin UI** | Interest rate, savings max, lock period, PIN, idle timeout — everything. |
