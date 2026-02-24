"""Calendar blueprint — today dashboard + weekly calendar view."""
from datetime import date, datetime, time, timedelta

from flask import Blueprint, jsonify, render_template, request, session

from app.extensions import db
from app.models.calendar import CalendarEvent
from app.models.chore import Chore
from app.models.user import User
from app.services import google_cal

calendar_bp = Blueprint("calendar", __name__)


def _today_name():
    """Return today's day name (e.g. 'Monday')."""
    return date.today().strftime("%A")


def _event_on_day(event: dict, target_date: date) -> bool:
    """Return True if the event's start falls on target_date."""
    start = event.get("start_time", "")
    if not start:
        return False
    try:
        return date.fromisoformat(start[:10]) == target_date
    except (ValueError, TypeError):
        return False


# ── page routes ───────────────────────────────────────────────────────

@calendar_bp.route("/today")
def today_page():
    """Render the daily Today dashboard."""
    user_id = session.get("current_user_id")
    if not user_id:
        return render_template("today.html", active_nav="today")

    # Fire calendar_explorer achievement on first visit
    try:
        from app.models.achievement import UserAchievement
        from app.services.achievements import check_achievements
        check_achievements(user_id, "today_page_visit")
    except Exception:
        pass

    return render_template("today.html", active_nav="today")


@calendar_bp.route("/calendar")
def calendar_page():
    """Render the weekly calendar view."""
    user_id = session.get("current_user_id")
    if not user_id:
        return render_template("calendar_weekly.html", active_nav="calendar")

    # Fire calendar_explorer achievement on first visit to weekly calendar
    try:
        from app.services.achievements import check_achievements
        check_achievements(user_id, "calendar_explorer")
    except Exception:
        pass

    return render_template("calendar_weekly.html", active_nav="calendar")


# ── API routes ────────────────────────────────────────────────────────

@calendar_bp.route("/api/calendar/today")
def today_data():
    """JSON endpoint: today's merged calendar + chore data for current user."""
    user_id = session.get("current_user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    today = date.today()
    day_name = today.strftime("%A")

    # Google Calendar events
    google_events = google_cal.get_todays_events(today)

    # Local calendar events for today
    local_events = CalendarEvent.query.filter_by(event_date=today).order_by(
        CalendarEvent.event_time.asc()
    ).all()

    # Current user's chores for today
    chores = Chore.query.filter_by(user_id=user_id, day=day_name).all()

    # Completion stats for today
    total = len(chores)
    done = sum(1 for c in chores if c.completed)

    return jsonify({
        "date": today.isoformat(),
        "day_name": day_name,
        "user": {"id": user.id, "username": user.username},
        "streak_current": user.streak_current,
        "streak_best": user.streak_best,
        "google_events": google_events,
        "local_events": [e.to_dict() for e in local_events],
        "chores": [
            {
                "id": c.id,
                "description": c.description,
                "completed": c.completed,
            }
            for c in chores
        ],
        "progress": {"total": total, "done": done},
    })


@calendar_bp.route("/api/calendar/week")
def week_data():
    """JSON endpoint: a 7-day week of calendar events, Mon–Sun."""
    user_id = session.get("current_user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    # Parse start date, normalize to Monday
    start_str = request.args.get("start", "")
    try:
        parsed = date.fromisoformat(start_str)
        # Normalize to Monday of that week
        week_start = parsed - timedelta(days=parsed.weekday())
    except (ValueError, TypeError):
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

    week_end = week_start + timedelta(days=6)

    # Fetch Google Calendar events for the whole week
    google_events = google_cal.get_week_events(week_start, week_end)

    today = date.today()
    days = []
    for i in range(7):
        day_date = week_start + timedelta(days=i)

        # Google events for this day
        day_google_events = [e for e in google_events if _event_on_day(e, day_date)]

        # Local events for this day
        local_events_db = CalendarEvent.query.filter_by(
            event_date=day_date
        ).order_by(CalendarEvent.event_time.asc()).all()

        # Convert local events to same structure as Google events
        day_local_events = []
        for e in local_events_db:
            time_str = e.event_time.strftime("%H:%M") if e.event_time else ""
            day_local_events.append({
                "title": e.title,
                "start_time": time_str,
                "end_time": "",
                "description": e.description or "",
                "google_event_id": None,
                "colorId": "",
                "color_hex": "#46d6db",  # peacock for local events
                "local_id": e.id,
            })

        days.append({
            "date": day_date.isoformat(),
            "day_name": day_date.strftime("%A"),
            "is_today": day_date == today,
            "events": day_google_events + day_local_events,
        })

    return jsonify({
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "days": days,
    })


@calendar_bp.route("/calendar/events", methods=["POST"])
def create_event():
    """Create a calendar event (local DB + optionally push to Google)."""
    user_id = session.get("current_user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "Title is required"}), 400

    event_date_str = data.get("event_date", "")
    try:
        event_date = date.fromisoformat(event_date_str)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid date format (use YYYY-MM-DD)"}), 400

    event_time = None
    time_str = data.get("event_time", "")
    if time_str:
        try:
            parsed = datetime.strptime(time_str, "%H:%M")
            event_time = time(parsed.hour, parsed.minute)
        except ValueError:
            return jsonify({"error": "Invalid time format (use HH:MM)"}), 400

    description = (data.get("description") or "").strip()

    # Push to Google Calendar
    google_event_id = google_cal.create_event(
        title=title,
        event_date=event_date,
        event_time=event_time,
        description=description,
    )

    # Save locally
    event = CalendarEvent(
        title=title,
        description=description or None,
        event_date=event_date,
        event_time=event_time,
        created_by=user_id,
        google_event_id=google_event_id,
    )
    db.session.add(event)
    db.session.commit()

    return jsonify(event.to_dict()), 201


@calendar_bp.route("/calendar/events/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    """Delete a calendar event (local DB + Google if synced)."""
    user_id = session.get("current_user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    event = db.session.get(CalendarEvent, event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    # Delete from Google if synced
    if event.google_event_id:
        google_cal.delete_event(event.google_event_id)

    db.session.delete(event)
    db.session.commit()

    return jsonify({"deleted": True})
