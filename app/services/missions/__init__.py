"""Mission handler registry.

Each mission type registers a handler class. The handler implements
training, testing, and progress logic specific to that mission type.
"""

from app.services.missions.multiplication import MultiplicationHandler
from app.services.missions.piano import PianoHandler

# Registry: mission_type string → handler instance
MISSION_HANDLERS = {
    "multiplication": MultiplicationHandler(),
    "piano": PianoHandler(),
}


def get_handler(mission_type):
    """Return the handler for a given mission type, or None."""
    return MISSION_HANDLERS.get(mission_type)
