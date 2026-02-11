# Project Home V2 — Testing Plan

> Last updated: 2026-02-09

---

## Testing Philosophy

Tests are written **alongside each phase**, not after. Every feature merged into the `v2` branch must include tests. The goal is confidence to ship — not 100% coverage for its own sake.

**Three testing layers:**
1. **Unit tests** (pytest) — Pure logic: calculations, state machines, data transforms
2. **API tests** (pytest + Flask test client) — Endpoint behavior: status codes, response shapes, auth, validation
3. **E2E tests** (Playwright) — Full browser flows: login, navigate, interact, verify visual state

**What gets tested at which layer:**
| Concern | Unit | API | E2E |
|---------|------|-----|-----|
| Interest calculation math | x | | |
| Allowance tier logic | x | | |
| XP/level threshold logic | x | | |
| Mission state machine transitions | x | | |
| Multiplication adaptive weighting | x | | |
| Streak calculation | x | | |
| PIN validation + rate limiting | | x | |
| Chore CRUD endpoints | | x | |
| Bank cashout endpoint | | x | |
| Savings lock/unlock logic | x | x | |
| IP trust middleware | | x | |
| Session timeout | | | x |
| Login → calendar flow | | | x |
| Chore check-off + confetti | | | x |
| Bank page interest ticker | | | x |
| Mission training session | | | x |
| Achievement notification display | | | x |
| Cashout confirmation modal | | | x |
| Admin dashboard operations | | x | x |
| Google Calendar integration | | x | |
| Weekly reset (full cycle) | | x | |
| Nav bar interest ticker | | | x |

---

## Testing Stack

### Tools
| Tool | Purpose |
|------|---------|
| **pytest** | Test runner, fixtures, assertions |
| **pytest-cov** | Code coverage reporting |
| **pytest-flask** | Flask test client helpers, app fixture |
| **pytest-mock** | Mock/patch for external services (Mailgun, Google Calendar) |
| **playwright** | Browser-based E2E testing |
| **pytest-playwright** | Playwright integration with pytest |
| **factory-boy** | Test data factories for DB models |
| **freezegun** | Time freezing for interest calculations, lock periods, timeouts |

### Directory structure
```
tests/
├── conftest.py              # Shared fixtures: app, db, client, test users
├── factories.py             # factory-boy model factories
├── unit/
│   ├── test_interest.py     # Interest calculation math
│   ├── test_allowance.py    # Allowance tier logic
│   ├── test_xp.py           # XP grants, level thresholds, 2x bonus
│   ├── test_streaks.py      # Streak increment/reset logic
│   ├── test_mission_sm.py   # Mission state machine transitions
│   ├── test_multiplication.py  # Adaptive weighting, readiness check
│   └── test_savings.py      # Lock period logic, withdrawal eligibility
├── api/
│   ├── test_auth.py         # PIN validation, IP trust, rate limiting
│   ├── test_session.py      # Login, logout, switch user, idle timeout
│   ├── test_chores.py       # Chore CRUD, completion, weekly reset
│   ├── test_grocery.py      # Grocery CRUD, send email
│   ├── test_calendar.py     # Event CRUD, Google Calendar mock
│   ├── test_bank.py         # Cashout, savings deposit/withdraw, transactions
│   ├── test_missions.py     # Mission CRUD, training, testing, approval
│   ├── test_achievements.py # Achievement triggers, XP grants
│   ├── test_users.py        # User CRUD, profile updates
│   ├── test_admin.py        # Admin dashboard, config editing, data export
│   └── test_weekly_reset.py # Full weekly reset cycle
└── e2e/
    ├── conftest.py          # Playwright fixtures, live server setup
    ├── test_login_flow.py   # PIN entry → user select → calendar
    ├── test_chore_flow.py   # View chores, check off, confetti, progress bar
    ├── test_calendar_flow.py # View events, create event, check off chore
    ├── test_bank_flow.py    # View balance, deposit savings, cashout, ticker
    ├── test_mission_flow.py # Start training, answer questions, take test
    ├── test_profile_flow.py # Change icon, theme, view achievements
    ├── test_navigation.py   # Bottom nav, switch user, idle timeout snap-back
    └── test_admin_flow.py   # Admin dashboard, assign mission, edit config
```

---

## Phase-by-Phase Test Plan

### Phase 1: Foundation, Security & Login

**Unit tests:**
- None yet (pure infrastructure)

**API tests:**
```
test_auth.py:
  - test_untrusted_ip_redirects_to_pin
  - test_correct_pin_trusts_ip
  - test_wrong_pin_rejected
  - test_pin_lockout_after_5_attempts
  - test_lockout_expires_after_15_minutes
  - test_trusted_ip_allows_access
  - test_expired_ip_requires_pin_again
  - test_static_files_exempt_from_auth

test_session.py:
  - test_login_sets_session_user
  - test_logout_clears_session
  - test_switch_user_changes_session
  - test_no_session_redirects_to_login
  - test_session_contains_user_id

test_chores.py (migration validation — V1 functionality preserved):
  - test_get_chores_filtered_by_user
  - test_create_chore
  - test_update_chore_completion
  - test_delete_chore
  - test_move_chore
  - test_rotating_chore_rotation

test_grocery.py:
  - test_grocery_crud (V1 parity)
  - test_grocery_shared_across_users

test_users.py:
  - test_create_user
  - test_delete_user_admin_only
  - test_user_has_migrated_email_and_allowance
```

**E2E tests:**
```
test_login_flow.py:
  - test_pin_page_shown_for_new_ip
  - test_pin_entry_grants_access
  - test_user_selection_screen_shows_all_users
  - test_user_selection_shows_levels
  - test_tap_user_goes_to_calendar
  - test_switch_user_returns_to_login
  - test_idle_timeout_snaps_back (wait 5+ min or mock timer)

test_navigation.py:
  - test_bottom_nav_links_work
  - test_current_user_shown_in_nav
  - test_switch_user_button_visible_everywhere
```

### Phase 2: Calendar Dashboard & Streaks

**Unit tests:**
```
test_streaks.py:
  - test_100_percent_increments_streak
  - test_less_than_100_resets_streak
  - test_streak_best_updated_on_new_record
  - test_streak_not_updated_when_no_chores
```

**API tests:**
```
test_calendar.py:
  - test_get_todays_events_merges_google_and_local
  - test_create_local_event_pushes_to_google (mocked)
  - test_delete_event_removes_from_google (mocked)
  - test_create_event_validation (title required, date required)
  - test_events_sorted_chronologically

test_chores.py (additions):
  - test_calendar_shows_only_todays_chores
  - test_chore_checkoff_from_calendar_endpoint
```

**E2E tests:**
```
test_calendar_flow.py:
  - test_calendar_shows_today_date
  - test_events_and_chores_in_separate_sections
  - test_create_event_appears_on_page
  - test_delete_event_removes_from_page
  - test_check_off_chore_from_calendar
  - test_streak_counter_displayed
```

### Phase 3: Bank & Allowance

**Unit tests:**
```
test_interest.py:
  - test_weekly_interest_calculation_basic
  - test_interest_with_multiple_deposits
  - test_interest_on_locked_deposits
  - test_interest_on_unlocked_deposits
  - test_interest_stops_on_withdrawn_deposits
  - test_interest_respects_savings_max
  - test_per_second_interest_rate_derivation
  - test_interest_ticker_calculation_matches_server

test_allowance.py:
  - test_100_percent_gets_full_allowance
  - test_50_percent_gets_half
  - test_below_50_gets_zero
  - test_zero_chores_gets_zero
  - test_edge_case_exactly_50_percent

test_savings.py:
  - test_deposit_creates_lock_period
  - test_deposit_rejected_over_max
  - test_deposit_rejected_under_minimum
  - test_withdrawal_rejected_while_locked
  - test_withdrawal_allowed_after_lock_expires
  - test_partial_withdrawal_of_unlocked_deposits
  - test_cashout_draws_cash_first_then_unlocked_savings
  - test_cashout_total_is_cash_plus_unlocked
  - test_cashout_rejected_under_minimum
```

**API tests:**
```
test_bank.py:
  - test_get_bank_page_returns_balances
  - test_deposit_to_savings_deducts_cash
  - test_deposit_to_savings_creates_deposit_record
  - test_deposit_to_savings_records_transaction
  - test_cashout_zeros_cash_and_withdraws_unlocked
  - test_cashout_sends_email (mocked Mailgun)
  - test_cashout_records_transaction
  - test_cashout_increments_total_cashed_out
  - test_cashout_confirmation_required
  - test_savings_goal_crud
  - test_transactions_endpoint_paginated
  - test_stats_endpoint_returns_totals
  - test_ticker_data_endpoint

test_weekly_reset.py:
  - test_reset_deposits_allowance_to_cash
  - test_reset_credits_interest
  - test_reset_records_transactions
  - test_reset_expires_old_ips
  - test_reset_sends_digest_email (mocked)
  - test_reset_calculates_correct_allowance_tier
  - test_reset_doubles_xp_for_100_percent
```

**E2E tests:**
```
test_bank_flow.py:
  - test_bank_page_shows_cash_balance
  - test_bank_page_shows_savings_deposits
  - test_interest_ticker_ticking_in_realtime
  - test_nav_bar_ticker_visible_on_all_pages
  - test_deposit_to_savings_flow
  - test_cashout_flow_with_confirmation
  - test_locked_deposit_shows_countdown
  - test_unlocked_deposit_shows_withdraw_option
  - test_savings_goal_progress_bar
  - test_transaction_history_tab
  - test_weekly_report_section
```

### Phase 4: Missions

**Unit tests:**
```
test_mission_sm.py:
  - test_initial_state_is_assigned
  - test_assigned_to_training
  - test_training_to_training (repeat)
  - test_training_to_ready_for_test
  - test_ready_to_testing
  - test_testing_to_completed
  - test_testing_to_failed_to_training
  - test_piano_testing_to_pending_approval
  - test_pending_approval_to_completed
  - test_pending_approval_rejected_to_training
  - test_invalid_state_transition_raises_error

test_multiplication.py:
  - test_generate_problems_in_range_1_to_12
  - test_adaptive_weighting_increases_weak_facts
  - test_readiness_check_85_percent_threshold
  - test_readiness_requires_3_sessions
  - test_test_pass_at_35_correct_in_60_seconds
  - test_test_fail_under_35_correct
  - test_session_length_options_10_20_30
  - test_wrong_answer_tracking
```

**API tests:**
```
test_missions.py:
  - test_admin_can_create_mission
  - test_admin_can_assign_mission
  - test_non_admin_cannot_assign
  - test_start_training_changes_state
  - test_submit_training_records_progress
  - test_get_training_session_returns_problems
  - test_submit_test_pass_completes_mission
  - test_submit_test_fail_returns_to_training
  - test_mission_completion_grants_cash_reward
  - test_mission_completion_grants_icon
  - test_piano_requires_admin_approval
  - test_admin_approve_completes_piano
  - test_admin_reject_returns_to_training
```

**E2E tests:**
```
test_mission_flow.py:
  - test_mission_hub_shows_active_missions
  - test_start_multiplication_training
  - test_training_session_shows_problems
  - test_answer_problems_and_see_score
  - test_choose_session_length
  - test_ready_for_test_notification
  - test_take_test_with_timer
  - test_mission_completion_celebration (fireworks, icon display)
  - test_mission_icon_auto_equipped
```

### Phase 5: Achievements, XP & Gamification

**Unit tests:**
```
test_xp.py:
  - test_chore_completion_grants_10_xp
  - test_100_percent_week_doubles_chore_xp
  - test_mission_completion_grants_500_xp
  - test_achievement_xp_granted
  - test_level_up_at_correct_thresholds
  - test_level_2_at_100_xp
  - test_level_5_at_850_xp
  - test_level_10_at_5000_xp
  - test_no_level_down
  - test_xp_accumulates_across_sources
```

**API tests:**
```
test_achievements.py:
  - test_first_chore_triggers_first_steps
  - test_streak_7_triggers_streak_starter
  - test_savings_max_triggers_savings_pro
  - test_first_cashout_triggers_achievement
  - test_achievement_not_double_granted
  - test_achievement_catalog_shows_all
  - test_locked_achievements_visible_with_requirements
  - test_achievement_grants_xp_not_icons
```

**E2E tests:**
```
test_profile_flow.py:
  - test_profile_shows_level_and_xp_bar
  - test_achievement_catalog_page
  - test_locked_achievements_greyed_out
  - test_icon_picker_shows_tiers (starter, level-unlocked, mission)
  - test_theme_color_picker_changes_accent
  - test_level_up_celebration_animation
  - test_bronze_achievement_shows_toast
  - test_gold_achievement_shows_fullscreen
  - test_login_screen_shows_level_effects
```

### Phase 6: Admin, Polish & Launch

**API tests:**
```
test_admin.py:
  - test_admin_dashboard_shows_all_users
  - test_non_admin_cannot_access_admin
  - test_edit_config_value
  - test_edit_pin_updates_hash
  - test_revoke_trusted_ip
  - test_create_user_from_admin
  - test_delete_user_from_admin
  - test_export_transactions_csv
  - test_export_chore_history_csv
  - test_export_all_json
```

**E2E tests:**
```
test_admin_flow.py:
  - test_admin_dashboard_family_overview
  - test_assign_mission_from_admin
  - test_approve_piano_mission
  - test_edit_interest_rate
  - test_revoke_ip_from_admin
  - test_data_export_downloads_file
```

---

## Testing Conventions

### Naming
- Test files: `test_<module>.py`
- Test functions: `test_<behavior_being_tested>`
- Descriptive names that read as specifications

### Fixtures (conftest.py)
- `app` — Flask app configured for testing (SQLite in-memory, testing=True)
- `db` — Fresh database per test (tables created, dropped after)
- `client` — Flask test client
- `auth_client` — Test client with a trusted IP (bypasses PIN)
- `logged_in_client(user)` — Test client with a specific user session
- `admin_client` — Test client logged in as admin user
- `sample_users` — Creates the 5 family members with correct allowances
- `sample_chores` — Creates a set of test chores
- `sample_bank` — Creates bank accounts with balances

### Factories (factory-boy)
- `UserFactory` — creates users with sensible defaults
- `ChoreFactory` — creates chores assigned to users
- `SavingsDepositFactory` — creates deposits with configurable lock periods
- `TransactionFactory` — creates transaction records
- `MissionFactory` / `MissionAssignmentFactory`
- `AchievementFactory`

### Mocks
External services are always mocked in tests:
- **Mailgun API** — mock `_send_email()`, capture sent messages for assertion
- **Google Calendar API** — mock the service client, return canned responses
- **Time** — use `freezegun` for interest calculations, lock periods, idle timeout

### Running tests
```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# API tests only
pytest tests/api/

# E2E tests only
pytest tests/e2e/

# With coverage
pytest --cov=app --cov-report=html

# Specific phase (using markers)
pytest -m phase1
pytest -m phase3

# Specific test file
pytest tests/api/test_bank.py

# Verbose with print output
pytest -v -s
```

### Pytest markers
```python
# In pytest.ini or pyproject.toml:
[tool:pytest]
markers =
    phase1: Phase 1 - Foundation & Security
    phase2: Phase 2 - Calendar & Streaks
    phase3: Phase 3 - Bank & Allowance
    phase4: Phase 4 - Missions
    phase5: Phase 5 - Achievements & Gamification
    phase6: Phase 6 - Admin & Polish
    e2e: End-to-end browser tests (requires Playwright)
    slow: Tests that take more than a few seconds
```

### E2E test approach
- Playwright runs a **live Flask dev server** on a random port for each test session
- Uses an **in-memory SQLite database** (no production data)
- Fixtures seed the DB with test data before each test
- Tests use **Playwright's auto-waiting** — no manual sleeps
- Screenshots captured on failure for debugging
- Tests tagged with `@pytest.mark.e2e` so they can be excluded from fast CI runs

### Coverage targets
| Layer | Target |
|-------|--------|
| Unit (calculations, state machines) | 95%+ |
| API (endpoints, auth) | 85%+ |
| E2E (critical flows) | Key happy paths + major error paths |
| Overall | 80%+ |

---

## Test Data Strategy

### Standard test users
| Username | Allowance | Admin | Level |
|----------|-----------|-------|-------|
| TestDad | 0 | Yes | 1 |
| TestKid1 | 15 | No | 1 |
| TestKid2 | 15 | No | 1 |

### Standard test chores
- 3 static chores per kid across Mon/Wed/Fri
- 1 rotating chore shared between kids

### Standard bank state
- TestKid1: $25 cash, 2 savings deposits ($10 locked, $10 unlocked)
- TestKid2: $0 cash, no savings

This provides a realistic base for testing bank operations without complex setup.
