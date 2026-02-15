"""Mailgun email service (V2-native).

Uses current_app.config for credentials instead of os.getenv.
Dry-runs (prints to stdout) when MAILGUN_API_KEY or MAILGUN_DOMAIN are empty.
"""

import requests
from flask import current_app


def send_email(to: str, subject: str, body: str) -> None:
    """Send a plain-text email via Mailgun.

    Args:
        to: recipient email address
        subject: email subject line
        body: plain-text email body
    """
    api_key = current_app.config.get("MAILGUN_API_KEY", "")
    domain = current_app.config.get("MAILGUN_DOMAIN", "")
    base_url = current_app.config.get(
        "MAILGUN_BASE_URL", "https://api.mailgun.net"
    )

    if not api_key or not domain:
        current_app.logger.info(
            "EMAIL (dry-run) To=%s Subject=%s\n%s", to, subject, body
        )
        return

    resp = requests.post(
        f"{base_url}/v3/{domain}/messages",
        auth=("api", api_key),
        data={
            "from": f"Felker Family Hub <mailgun@{domain}>",
            "to": [to],
            "subject": subject,
            "text": body,
        },
        timeout=15,
    )

    if resp.status_code >= 400:
        current_app.logger.error(
            "Mailgun error %d: %s", resp.status_code, resp.text
        )
        raise RuntimeError(
            f"Mailgun error {resp.status_code}: {resp.text}"
        )
