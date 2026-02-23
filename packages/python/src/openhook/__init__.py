"""OpenHook Protocol SDK for Python."""

from .compat import from_legacy, is_openhook
from .envelope import OpenHookEvent, ValidationError, parse_stdin, validate
from .events import EventType

__all__ = [
    "EventType",
    "OpenHookEvent",
    "ValidationError",
    "from_legacy",
    "is_openhook",
    "parse_stdin",
    "validate",
]
