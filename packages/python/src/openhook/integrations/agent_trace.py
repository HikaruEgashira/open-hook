"""Bridge utilities for Agent Trace (https://agent-trace.dev/) integration.

Agent Trace is an open specification for tracking AI-generated code.
This module converts OpenHook file.write events into Agent Trace TraceRecords.

Example::

    from openhook import parse_stdin
    from openhook.integrations.agent_trace import to_trace_record
    import json

    event = parse_stdin()
    record = to_trace_record(event)
    if record:
        print(json.dumps(record))
"""

from __future__ import annotations

import uuid
from typing import Any

from openhook.envelope import OpenHookEvent
from openhook.events import EventType


def to_trace_record(event: OpenHookEvent) -> dict[str, Any] | None:
    """Convert a file.write OpenHook event to an Agent Trace TraceRecord.

    Returns None if the event is not a file.write event or lacks a path.
    See https://agent-trace.dev/ for the full TraceRecord specification.
    """
    if event.type != EventType.FILE_WRITE:
        return None

    path: str | None = event.data.get("path")
    if not path:
        return None

    model: str | None = event.data.get("model")
    contributor: dict[str, Any] = {"type": "ai"}
    if model:
        contributor["model"] = model

    conversation: dict[str, Any] = {"contributor": contributor}
    start_line = event.data.get("start_line")
    end_line = event.data.get("end_line")
    if start_line and end_line:
        conversation["ranges"] = [{"start_line": start_line, "end_line": end_line}]

    return {
        "version": "0.1.0",
        "id": str(uuid.uuid4()),
        "timestamp": event.time,
        "files": [{"path": path, "conversations": [conversation]}],
        "tool": {
            "name": event.source,
            "session_id": event.session_id,
        },
    }
