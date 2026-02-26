"""Standard OpenHook event types."""

from enum import StrEnum


class EventType(StrEnum):
    SESSION_START = "session.start"
    SESSION_END = "session.end"
    PROMPT_SUBMIT = "prompt.submit"
    TOOL_START = "tool.start"
    TOOL_END = "tool.end"
    FILE_WRITE = "file.write"


ALL_EVENT_TYPES = frozenset(EventType)
