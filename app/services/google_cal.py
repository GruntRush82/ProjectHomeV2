"""Google Calendar integration service.

Uses a service account to read/write events. Gracefully degrades
if credentials are not configured — all methods return empty results
or no-ops instead of raising.
"""
import logging
import time
from datetime import date, datetime, timedelta

from flask import current_app

log = logging.getLogger(__name__)

# Google Calendar colorId → hex mapping
GOOGLE_COLOR_MAP = {
    "1":  "#a4bdfc",  # lavender
    "2":  "#7ae7bf",  # sage
    "3":  "#dbadff",  # grape
    "4":  "#ff887c",  # flamingo
    "5":  "#fbd75b",  # banana
    "6":  "#ffb878",  # tangerine
    "7":  "#46d6db",  # peacock
    "8":  "#e1e1e1",  # graphite
    "9":  "#5484ed",  # blueberry
    "10": "#51b749",  # basil
    "11": "#dc2127",  # tomato
}

# --------------- in-memory cache ---------------
_cache = {}
_CACHE_TTL = 15 * 60  # 15 minutes


def _cache_key(calendar_id: str, day: date) -> str:
    return f"{calendar_id}:{day.isoformat()}"


def _get_cached(key: str):
    entry = _cache.get(key)
    if entry and time.time() - entry["ts"] < _CACHE_TTL:
        return entry["data"]
    return None


def _set_cached(key: str, data):
    _cache[key] = {"data": data, "ts": time.time()}


def invalidate_cache(calendar_id: str = None):
    """Clear cache. If calendar_id given, only clear that calendar's entries."""
    if calendar_id is None:
        _cache.clear()
    else:
        keys = [k for k in _cache if k.startswith(calendar_id + ":")]
        for k in keys:
            del _cache[k]


# --------------- service client ---------------
def _build_service():
    """Build the Google Calendar API service client.

    Returns None if credentials are not configured.
    """
    json_path = current_app.config.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not json_path:
        return None

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds = service_account.Credentials.from_service_account_file(
            json_path,
            scopes=["https://www.googleapis.com/auth/calendar"],
        )
        return build("calendar", "v3", credentials=creds, cache_discovery=False)
    except Exception:
        log.exception("Failed to build Google Calendar service")
        return None


def _get_calendar_id() -> str:
    return current_app.config.get("GOOGLE_CALENDAR_ID", "")


# --------------- public API ---------------
def get_todays_events(target_date: date = None):
    """Fetch events for a given date from Google Calendar.

    Returns a list of dicts: {title, start_time, end_time, description, google_event_id}
    Returns empty list if credentials not configured or on error.
    """
    if target_date is None:
        target_date = date.today()

    calendar_id = _get_calendar_id()
    if not calendar_id:
        return []

    key = _cache_key(calendar_id, target_date)
    cached = _get_cached(key)
    if cached is not None:
        return cached

    service = _build_service()
    if service is None:
        return []

    try:
        time_min = datetime.combine(target_date, datetime.min.time()).isoformat() + "Z"
        time_max = datetime.combine(target_date + timedelta(days=1), datetime.min.time()).isoformat() + "Z"

        result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = []
        for item in result.get("items", []):
            start = item.get("start", {})
            end = item.get("end", {})
            color_id = item.get("colorId", "")
            events.append(
                {
                    "title": item.get("summary", "(No title)"),
                    "start_time": start.get("dateTime", start.get("date", "")),
                    "end_time": end.get("dateTime", end.get("date", "")),
                    "description": item.get("description", ""),
                    "google_event_id": item.get("id", ""),
                    "colorId": color_id,
                    "color_hex": GOOGLE_COLOR_MAP.get(color_id, "#5484ed"),
                }
            )

        _set_cached(key, events)
        return events

    except Exception:
        log.exception("Failed to fetch Google Calendar events")
        return []


def get_week_events(start_date: date, end_date: date):
    """Fetch events for a date range from Google Calendar.

    Returns a list of dicts: {title, start_time, end_time, description,
    google_event_id, colorId, color_hex}
    Returns empty list if credentials not configured or on error.
    """
    calendar_id = _get_calendar_id()
    if not calendar_id:
        return []

    key = f"{calendar_id}:week:{start_date.isoformat()}"
    cached = _get_cached(key)
    if cached is not None:
        return cached

    service = _build_service()
    if service is None:
        return []

    try:
        time_min = datetime.combine(start_date, datetime.min.time()).isoformat() + "Z"
        time_max = datetime.combine(end_date + timedelta(days=1), datetime.min.time()).isoformat() + "Z"

        result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = []
        for item in result.get("items", []):
            start = item.get("start", {})
            end = item.get("end", {})
            color_id = item.get("colorId", "")
            events.append(
                {
                    "title": item.get("summary", "(No title)"),
                    "start_time": start.get("dateTime", start.get("date", "")),
                    "end_time": end.get("dateTime", end.get("date", "")),
                    "description": item.get("description", ""),
                    "google_event_id": item.get("id", ""),
                    "colorId": color_id,
                    "color_hex": GOOGLE_COLOR_MAP.get(color_id, "#5484ed"),
                }
            )

        _set_cached(key, events)
        return events

    except Exception:
        log.exception("Failed to fetch Google Calendar week events")
        return []


def create_event(title: str, event_date: date, event_time=None, description: str = ""):
    """Create an event on Google Calendar.

    Returns the Google event ID string, or None on failure / no credentials.
    """
    calendar_id = _get_calendar_id()
    service = _build_service()
    if not calendar_id or service is None:
        return None

    try:
        if event_time:
            start_dt = datetime.combine(event_date, event_time)
            end_dt = start_dt + timedelta(hours=1)
            body = {
                "summary": title,
                "description": description,
                "start": {"dateTime": start_dt.isoformat(), "timeZone": "America/Chicago"},
                "end": {"dateTime": end_dt.isoformat(), "timeZone": "America/Chicago"},
            }
        else:
            body = {
                "summary": title,
                "description": description,
                "start": {"date": event_date.isoformat()},
                "end": {"date": (event_date + timedelta(days=1)).isoformat()},
            }

        event = service.events().insert(calendarId=calendar_id, body=body).execute()
        invalidate_cache(calendar_id)
        return event.get("id")

    except Exception:
        log.exception("Failed to create Google Calendar event")
        return None


def delete_event(google_event_id: str):
    """Delete an event from Google Calendar.

    Returns True on success, False on failure / no credentials.
    """
    calendar_id = _get_calendar_id()
    service = _build_service()
    if not calendar_id or service is None or not google_event_id:
        return False

    try:
        service.events().delete(calendarId=calendar_id, eventId=google_event_id).execute()
        invalidate_cache(calendar_id)
        return True
    except Exception:
        log.exception("Failed to delete Google Calendar event")
        return False
