"""
Visual test battery for Felker Family Hub.

Runs Playwright against the local dev server, captures screenshots for human /
Claude review, and asserts key structural + functional requirements.

Usage (from project root, venv activated):
    python tests/visual_tests.py [--base-url http://localhost:5000]

Output:
    screenshots/visual_<timestamp>/   — all captured screenshots
    screenshots/visual_<timestamp>/report.txt — pass/fail summary

Run this at the end of every phase or any time you want a visual sanity check.
"""

import argparse
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, Browser


# ── Config ────────────────────────────────────────────────────────────────

BASE_URL = "http://localhost:5000"
VIEWPORT = {"width": 1024, "height": 768}       # iPad landscape
SCREENSHOT_DIR = Path(__file__).parent.parent / "screenshots"

# Users to test with (must exist in local DB)
LOGIN_USER = "Calvin"           # primary test user (L10 for full effects)
ADMIN_USER = "Travis"           # admin user for admin-only tests

# ── Helpers ───────────────────────────────────────────────────────────────

results: list[dict] = []


def _pass(name: str, note: str = ""):
    results.append({"name": name, "status": "PASS", "note": note})
    print(f"  ✓  {name}" + (f"  [{note}]" if note else ""))


def _fail(name: str, reason: str):
    results.append({"name": name, "status": "FAIL", "note": reason})
    print(f"  ✗  {name}  — {reason}")


def _shot(page: Page, out_dir: Path, name: str, clip: dict | None = None):
    """Save a screenshot and return the path."""
    path = out_dir / f"{name}.png"
    page.screenshot(path=str(path), full_page=(clip is None), clip=clip)
    return path


def _element_shot(page: Page, out_dir: Path, name: str, selector: str):
    """Screenshot of a single element (best-effort)."""
    try:
        el = page.locator(selector).first
        box = el.bounding_box()
        if box:
            pad = 12
            _shot(page, out_dir, name, clip={
                "x": max(0, box["x"] - pad), "y": max(0, box["y"] - pad),
                "width": box["width"] + pad * 2, "height": box["height"] + pad * 2,
            })
    except Exception:
        pass   # non-fatal — screenshot failures don't fail the test


def _login_as(page: Page, username: str):
    """Log out any current session then click the user card on the login page."""
    page.goto(BASE_URL + "/session/logout")
    page.wait_for_load_state("networkidle")
    page.goto(BASE_URL + "/")
    page.wait_for_load_state("networkidle")
    page.locator(".user-card-form").filter(has_text=username).first.click()
    page.wait_for_load_state("networkidle")


def _check(condition: bool, name: str, fail_msg: str = "assertion failed"):
    if condition:
        _pass(name)
    else:
        _fail(name, fail_msg)


# ── Test sections ─────────────────────────────────────────────────────────

def test_login_page(page: Page, out_dir: Path):
    print("\n── Login page ──")
    page.goto(BASE_URL + "/")
    page.wait_for_load_state("networkidle")
    time.sleep(1)

    _shot(page, out_dir, "01_login_full")
    _check(page.locator(".user-grid").count() > 0, "login: user grid present")
    _check(page.locator(".user-card").count() >= 2, "login: at least 2 user cards")
    _check(page.title() != "", "login: page has a title")

    # Per-user card screenshots
    for card in page.locator(".user-card-form").all():
        name = card.locator(".user-card-name").text_content()
        if name:
            box = card.bounding_box()
            if box:
                page.screenshot(
                    path=str(out_dir / f"01_login_card_{name.lower()}.png"),
                    clip={"x": max(0, box["x"]-15), "y": max(0, box["y"]-15),
                          "width": box["width"]+30, "height": box["height"]+30},
                )

    # No JS errors: checked globally at the end


def test_calendar_page(page: Page, out_dir: Path):
    print("\n── Calendar page ──")
    _login_as(page, LOGIN_USER)
    page.goto(BASE_URL + "/calendar")
    page.wait_for_load_state("networkidle")
    time.sleep(1)

    _shot(page, out_dir, "02_calendar_full")
    _check(page.locator(".calendar-header").count() > 0, "calendar: header present")
    _check(page.locator(".calendar-section").count() >= 2, "calendar: 2 sections (chores + events)")

    # Chores section
    chore_items = page.locator(".calendar-section .chore-item")
    chore_count = chore_items.count()
    _check(True, f"calendar: {chore_count} chore(s) displayed")
    _element_shot(page, out_dir, "02_calendar_chores_section",
                  ".calendar-section:first-of-type")

    # Each chore item must be a <button>
    non_button = page.locator(".calendar-section .chore-item:not(button)").count()
    _check(non_button == 0, "calendar: all chore items are <button> elements",
           f"{non_button} chore(s) are not <button>")

    # Toggle first chore if any exist
    if chore_count > 0:
        first = chore_items.first
        was_done = "chore-done" in (first.get_attribute("class") or "")
        first.click()
        time.sleep(0.8)
        is_done_now = "chore-done" in (first.get_attribute("class") or "")
        _check(is_done_now != was_done, "calendar: chore toggle changes done state")
        _shot(page, out_dir, "02_calendar_after_toggle")
        # Toggle back
        first.click()
        time.sleep(0.5)

    # Events section
    _element_shot(page, out_dir, "02_calendar_events_section",
                  ".calendar-section:last-of-type")
    add_btn = page.locator(".add-event-btn")
    _check(add_btn.count() > 0, "calendar: add event button present")


def test_chores_page(page: Page, out_dir: Path):
    print("\n── Chores page ──")
    _login_as(page, LOGIN_USER)
    page.goto(BASE_URL + "/chores-page")
    page.wait_for_load_state("networkidle")
    time.sleep(1)

    _shot(page, out_dir, "03_chores_full")
    _check(page.locator("#chore-list, #tab-chores, .chore-list, [class*='chore']").count() > 0,
           "chores: grid container present")


def test_bank_page(page: Page, out_dir: Path):
    print("\n── Bank page ──")
    _login_as(page, LOGIN_USER)
    page.goto(BASE_URL + "/bank")
    page.wait_for_load_state("networkidle")
    time.sleep(1.5)

    _shot(page, out_dir, "04_bank_full")

    # Check cashout_available is returned by API (includes interest)
    resp = page.request.get(BASE_URL + "/api/bank/overview")
    _check(resp.ok, "bank: /api/bank/overview returns 200")
    if resp.ok:
        data = resp.json()
        _check("cashout_available" in data, "bank: cashout_available field present")
        _check("account" in data and "cash_balance" in data["account"],
               "bank: account.cash_balance field present")
        _check(isinstance(data.get("deposits"), list), "bank: deposits list present")
        # cashout_available should be >= cash_balance (because it includes unlocked savings)
        ca = data.get("cashout_available", -1)
        cb = data["account"].get("cash_balance", 0)
        _check(ca >= cb, "bank: cashout_available >= cash_balance",
               f"cashout_available={ca} < cash_balance={cb}")

    # Savings deposits — screenshot each ice crystal if any
    deposits = page.locator(".vault-item, .savings-deposit, [class*='deposit']").all()
    _check(True, f"bank: {len(deposits)} savings deposit card(s) visible")
    for i, dep in enumerate(deposits[:4]):   # cap at 4
        box = dep.bounding_box()
        if box:
            page.screenshot(
                path=str(out_dir / f"04_bank_deposit_{i+1}.png"),
                clip={"x": max(0, box["x"]-8), "y": max(0, box["y"]-8),
                      "width": box["width"]+16, "height": box["height"]+16},
            )

    # Nav ticker is visible
    _check(page.locator(".nav-ticker").count() > 0, "bank: nav ticker present")
    _element_shot(page, out_dir, "04_bank_nav_ticker", ".nav-ticker")


def test_profile_page(page: Page, out_dir: Path):
    print("\n── Profile page ──")
    _login_as(page, LOGIN_USER)
    page.goto(BASE_URL + "/profile")
    page.wait_for_load_state("networkidle")
    time.sleep(1.5)

    _shot(page, out_dir, "05_profile_full")

    # Avatar
    _check(page.locator(".profile-avatar, [class*='avatar']").count() > 0,
           "profile: avatar element present")
    _element_shot(page, out_dir, "05_profile_avatar", ".profile-avatar")

    # Level badge
    _element_shot(page, out_dir, "05_profile_level_badge",
                  ".level-badge, [class*='level-badge']")

    # Icon grid
    icon_count = page.locator(".icon-btn, [class*='icon-btn']").count()
    _check(icon_count >= 5, "profile: icon grid has at least 5 icons",
           f"found {icon_count}")
    _element_shot(page, out_dir, "05_profile_icon_grid", ".icon-grid, [class*='icon-grid']")

    # API: available_icons should be list of dicts with emoji/level
    resp = page.request.get(BASE_URL + "/api/profile")
    _check(resp.ok, "profile: /api/profile returns 200")
    if resp.ok:
        data = resp.json()
        icons = data.get("available_icons", [])
        _check(len(icons) >= 5, f"profile: API returns {len(icons)} icons")
        if icons:
            first = icons[0]
            _check("emoji" in first, "profile: icon dicts have 'emoji' key")
            _check("min_level" in first or "locked" in first,
                   "profile: icon dicts have level/locked info")

    # Achievement catalog section
    _element_shot(page, out_dir, "05_profile_achievements",
                  "[class*='achievement'], .achievement-catalog")


def test_missions_page(page: Page, out_dir: Path):
    print("\n── Missions page ──")
    _login_as(page, LOGIN_USER)
    page.goto(BASE_URL + "/missions")
    page.wait_for_load_state("networkidle")
    time.sleep(1)

    _shot(page, out_dir, "06_missions_full")
    _check(page.locator("h1, h2, .page-title").count() > 0, "missions: heading present")


def test_level_effects(page: Page, out_dir: Path):
    """Screenshot each user card to compare level visual effects."""
    print("\n── Level effect comparison ──")
    page.goto(BASE_URL + "/session/logout")
    page.wait_for_load_state("networkidle")
    page.goto(BASE_URL + "/")
    page.wait_for_load_state("networkidle")
    time.sleep(1.5)

    cards = page.locator(".user-card").all()
    for card in cards:
        level = card.get_attribute("data-level") or "?"
        name_el = card.locator(".user-card-name")
        name = name_el.text_content().strip() if name_el.count() > 0 else "unknown"
        avatar = card.locator(".user-card-avatar")
        if avatar.count() > 0:
            box = avatar.bounding_box()
            if box:
                page.screenshot(
                    path=str(out_dir / f"07_level_avatar_L{level.zfill(2)}_{name.lower()}.png"),
                    clip={"x": max(0, box["x"]-20), "y": max(0, box["y"]-20),
                          "width": box["width"]+40, "height": box["height"]+40},
                )
    _check(True, f"level effects: {len(cards)} avatar(s) captured")


def test_bottom_nav(page: Page, out_dir: Path):
    print("\n── Bottom nav bar ──")
    _login_as(page, LOGIN_USER)
    page.wait_for_load_state("networkidle")
    time.sleep(1)

    nav = page.locator(".bottom-nav")
    _check(nav.count() > 0, "nav: bottom nav present")
    if nav.count() > 0:
        box = nav.first.bounding_box()
        if box:
            page.screenshot(
                path=str(out_dir / "08_bottom_nav.png"),
                clip={"x": 0, "y": max(0, box["y"]-4),
                      "width": VIEWPORT["width"], "height": box["height"]+8},
            )
        # All 6 nav links present
        links = nav.first.locator("a.nav-item").count()
        _check(links == 6, f"nav: 6 nav items", f"found {links}")
        # Ticker present
        _check(nav.first.locator(".nav-ticker").count() > 0, "nav: ticker present")
        # User avatar in nav
        _check(nav.first.locator(".nav-user").count() > 0, "nav: user badge present")


def test_no_js_errors(page: Page, out_dir: Path, js_errors: list[str]):
    print("\n── JS error check ──")
    _check(len(js_errors) == 0, "no JS errors across all pages",
           f"{len(js_errors)} error(s): " + "; ".join(js_errors[:3]))


# ── Runner ────────────────────────────────────────────────────────────────

def run_all(base_url: str):
    global BASE_URL
    BASE_URL = base_url.rstrip("/")

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = SCREENSHOT_DIR / f"visual_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nVisual test run — {ts}")
    print(f"Server: {BASE_URL}")
    print(f"Output: {out_dir}\n")

    js_errors: list[str] = []

    with sync_playwright() as pw:
        browser: Browser = pw.chromium.launch()
        ctx = browser.new_context(viewport=VIEWPORT)
        page = ctx.new_page()

        # Collect JS console errors globally
        page.on("pageerror", lambda err: js_errors.append(str(err)))

        # Check server is up
        try:
            r = page.request.get(BASE_URL + "/")
            if not r.ok:
                print(f"ERROR: server returned {r.status} — is it running?")
                sys.exit(1)
        except Exception as e:
            print(f"ERROR: cannot reach {BASE_URL} — {e}")
            sys.exit(1)

        tests = [
            test_login_page,
            test_calendar_page,
            test_chores_page,
            test_bank_page,
            test_profile_page,
            test_missions_page,
            test_level_effects,
            test_bottom_nav,
        ]

        for test_fn in tests:
            try:
                test_fn(page, out_dir)
            except Exception as e:
                _fail(test_fn.__name__, f"uncaught exception: {e}")
                traceback.print_exc()

        test_no_js_errors(page, out_dir, js_errors)

        browser.close()

    # Write report
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    total = len(results)

    report_lines = [
        f"Visual Test Report — {ts}",
        f"Server: {BASE_URL}",
        f"Results: {passed}/{total} passed, {failed} failed",
        "",
    ]
    for r in results:
        icon = "✓" if r["status"] == "PASS" else "✗"
        line = f"{icon} [{r['status']}] {r['name']}"
        if r["note"]:
            line += f"  — {r['note']}"
        report_lines.append(line)

    report_path = out_dir / "report.txt"
    report_path.write_text("\n".join(report_lines) + "\n")

    print(f"\n{'─'*50}")
    print(f"Results: {passed}/{total} passed" + (f", {failed} FAILED" if failed else " — all good"))
    print(f"Screenshots + report: {out_dir}")
    if failed:
        print("\nFailed tests:")
        for r in results:
            if r["status"] == "FAIL":
                print(f"  ✗ {r['name']}: {r['note']}")

    return failed == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visual test suite for Family Hub")
    parser.add_argument("--base-url", default="http://localhost:5000",
                        help="Base URL of the running dev server")
    args = parser.parse_args()
    ok = run_all(args.base_url)
    sys.exit(0 if ok else 1)
