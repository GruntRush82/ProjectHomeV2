# reporting.py  – config sync + allowance & email draft (snapshot‑based)
"""Weekly reporting helper (snapshot edition).

Changes in this revision
------------------------
* **No “week” window** – report uses the *latest* archive snapshot
  (all `ChoreHistory` rows that share the most‑recent `date`).
* Logic elsewhere (scheduler / manual reset) stays the same; they always
  **archive first, then call** `generate_weekly_reports()`.
* Email wording adjusted: “snapshot of YYYY‑MM‑DD”.

Other functionality (config sync, allowance tiers, SMTP dry‑run etc.)
remains unchanged.
"""
from __future__ import annotations

import os
import requests
from email.utils import parseaddr
from dataclasses import dataclass
from datetime import date
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, Sequence

import yaml
from sqlalchemy import func

# ---------------------------------------------------------------------------
# config helpers
# ---------------------------------------------------------------------------

CONFIG_FILE = Path("reporting_config.yaml")
DEFAULT_USER_BLOCK: Dict[str, Any] = {"email": "", "allowance": 0}


def _load_config(path: Path = CONFIG_FILE) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf‑8") as fh:
        return yaml.safe_load(fh) or {}


def _save_config(data: Dict[str, Dict[str, Any]], path: Path = CONFIG_FILE) -> None:
    with path.open("w", encoding="utf‑8") as fh:
        yaml.dump(data, fh, sort_keys=True, default_flow_style=False, allow_unicode=True)


# ---------------------------------------------------------------------------
# public API – sync
# ---------------------------------------------------------------------------

def sync_config(db_session, *, path: Path | str = CONFIG_FILE) -> Dict[str, Dict[str, Any]]:
    """Synchronise *path* with DB users and return the dict."""
    from Family_Hub1_0 import User  # local import to avoid circular deps

    path = Path(path)
    cfg = _load_config(path)

    live_usernames = {u.username for u in db_session.query(User).all()}

    # add / update
    for name in live_usernames:
        block = cfg.setdefault(name, {})
        for k, v in DEFAULT_USER_BLOCK.items():
            block.setdefault(k, v)

    # hard‑prune removed users
    for name in list(cfg):
        if name not in live_usernames:
            del cfg[name]

    _save_config(cfg, path)
    return cfg


# ---------------------------------------------------------------------------
# allowance calculation
# ---------------------------------------------------------------------------

@dataclass
class SnapshotStats:
    total: int
    completed: int

    @property
    def pct(self) -> float:
        return 0.0 if self.total == 0 else self.completed / self.total


def calc_allowance(stats: SnapshotStats, full_amount: float | int) -> float:
    """Return the earned allowance based on the 100 / 50 / 0 rule."""
    if stats.pct >= 1.0:
        return full_amount
    if stats.pct >= 0.5:
        return full_amount * 0.5
    return 0.0


# ---------------------------------------------------------------------------
# e‑mail helpers
# ---------------------------------------------------------------------------

def _send_email(msg: EmailMessage) -> None:
    api_key = os.getenv("MAILGUN_API_KEY")
    domain = os.getenv("MAILGUN_DOMAIN")
    base_url = os.getenv("MAILGUN_BASE_URL", "https://api.mailgun.net")

    if not api_key or not domain:
        print("\n----- EMAIL (dry-run) -----")
        print(msg)
        print("----- END -----\n")
        return

    _, to_email = parseaddr(msg["To"])
    if not to_email:
        raise ValueError(f"Invalid To header: {msg['To']}")

    resp = requests.post(
        f"{base_url}/v3/{domain}/messages",
        auth=("api", api_key),
        data={
            "from": f"Family Hub <mailgun@{domain}>",
            "to": [to_email],
            "subject": msg["Subject"] or "",
            "text": msg.get_content(),
        },
        timeout=15,
    )

    if resp.status_code >= 400:
        raise RuntimeError(f"Mailgun error {resp.status_code}: {resp.text}")


def _format_report(
    user: str,
    stats: SnapshotStats,
    allowance: float,
    chores: Sequence[dict[str, Any]],
    *,
    snapshot_date: date,
) -> str:
    lines = [
        f"Hi {user},",
        "",
        f"Here’s your chore report – snapshot of {snapshot_date:%Y‑%m‑%d}.",
        f"You completed {stats.completed}/{stats.total} chores ({stats.pct:.0%}).",
        f"Earned allowance: ${allowance:.2f}",
        "",
        "Details:",
    ]
    for c in chores:
        mark = "✓" if c["completed"] else "✗"
        lines.append(f"  {mark} {c['day']:<9} – {c['description']}")
    lines.append("\nNice work!  — Family Hub")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# main entry: generate & dispatch snapshot reports
# ---------------------------------------------------------------------------

def generate_weekly_reports(db_session) -> None:  # keeping name for back‑compat
    """Send a report based on the *latest* ChoreHistory snapshot."""
    from Family_Hub1_0 import User, ChoreHistory  # local import

    latest: date | None = db_session.query(func.max(ChoreHistory.date)).scalar()
    if latest is None:
        print("No history rows yet – nothing to report.")
        return

    cfg = sync_config(db_session)

    # cache of rows for that snapshot, keyed by username
    rows_by_user: Dict[str, list[ChoreHistory]] = {}
    for row in (
        db_session.query(ChoreHistory)
        .filter(ChoreHistory.date == latest)
        .all()
    ):
        rows_by_user.setdefault(row.username, []).append(row)

    for user in db_session.query(User).all():
        hist = rows_by_user.get(user.username, [])
        if not hist:
            continue  # user had no chores at snapshot time

        block = cfg.get(user.username, DEFAULT_USER_BLOCK)
        full_allow = block.get("allowance", 0) or 0
        email_addr = (block.get("email") or "").strip()
        if not (full_allow and email_addr):
            continue  # user opted out / not configured yet

        stats = SnapshotStats(total=len(hist), completed=sum(1 for h in hist if h.completed))
        earned = calc_allowance(stats, full_allow)

        body = _format_report(
            user.username,
            stats,
            earned,
            [
                {
                    "day": h.day,
                    "description": h.chore.description if h.chore else "(deleted chore)",
                    "completed": h.completed,
                }
                for h in hist
            ],
            snapshot_date=latest,
        )

        msg = EmailMessage()
        msg["Subject"] = "Your weekly chore report"
        msg["To"] = email_addr
        msg.set_content(body)

        _send_email(msg)


# ---------------------------------------------------------------------------
# CLI helper
# ---------------------------------------------------------------------------

def main() -> None:  # type: ignore[override]
    """`python reporting.py [sync|report]` (defaults to *sync*)."""
    from sys import argv
    from Family_Hub1_0 import db, app

    cmd = (argv[1] if len(argv) > 1 else "sync").lower()

    with app.app_context():
        with db.session() as session:  # type: ignore[attr-defined]
            if cmd == "report":
                generate_weekly_reports(session)
            else:
                updated = sync_config(session)
                print(f"config synced → {len(updated)} user blocks")



if __name__ == "__main__":
    main()