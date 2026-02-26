"""Legacy payload conversion for otel-hooks migration."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from .envelope import OpenHookEvent
from .events import EventType

# Maps legacy hook_event_name -> OpenHook event type
_METRIC_EVENT_MAP: dict[str, EventType] = {
    "userPromptSubmitted": EventType.PROMPT_SUBMIT,
    "userPromptSubmit": EventType.PROMPT_SUBMIT,
    "preToolUse": EventType.TOOL_START,
    "postToolUse": EventType.TOOL_END,
    "sessionEnd": EventType.SESSION_END,
    "stop": EventType.SESSION_END,
}

# Legacy session ID field names in priority order
_SESSION_ID_KEYS = ("sessionId", "session_id", "conversation_id", "taskId", "thread-id")

# Legacy transcript path field names
_TRANSCRIPT_KEYS = ("transcriptPath", "transcript_path")


def _cwd_to_context(cwd: str) -> str:
    """Convert a legacy filesystem path to a file:// URI."""
    if "://" in cwd:
        return cwd
    return f"file://{cwd}"


def _detect_source(payload: dict[str, Any]) -> str:
    if payload.get("source_tool"):
        return str(payload["source_tool"])
    if "conversation_id" in payload:
        return "cursor"
    if "taskId" in payload:
        return "cline"
    if "thread-id" in payload:
        return "codex"
    if "hook_event_name" in payload:
        return "copilot"
    # Claude Code uses camelCase fields (sessionId, transcriptPath)
    # while other tools use snake_case (session_id)
    if "sessionId" in payload or "transcriptPath" in payload:
        return "claude-code"
    return "unknown"


def _extract_session_id(payload: dict[str, Any]) -> str:
    for key in _SESSION_ID_KEYS:
        if key in payload:
            return str(payload[key])
    nested = payload.get("session", {})
    if isinstance(nested, dict) and "id" in nested:
        return str(nested["id"])
    return ""


def _extract_transcript_path(payload: dict[str, Any]) -> str | None:
    for key in _TRANSCRIPT_KEYS:
        if key in payload:
            return str(payload[key])
    nested = payload.get("transcript", {})
    if isinstance(nested, dict) and "path" in nested:
        return str(nested["path"])
    return None


def from_legacy(payload: dict[str, Any]) -> OpenHookEvent:
    """Convert a legacy (non-OpenHook) hook payload to an OpenHookEvent."""
    source = _detect_source(payload)
    session_id = _extract_session_id(payload)
    now = datetime.now(timezone.utc).isoformat()

    hook_event = payload.get("hook_event_name", "")
    event_type = _METRIC_EVENT_MAP.get(hook_event, EventType.SESSION_END)

    data: dict[str, Any] = {}
    transcript = _extract_transcript_path(payload)
    if transcript:
        data["transcript_path"] = transcript

    if event_type == EventType.TOOL_START or event_type == EventType.TOOL_END:
        if "tool_name" in payload:
            data["tool_name"] = payload["tool_name"]

    raw_cwd = payload.get("cwd")
    context = _cwd_to_context(raw_cwd) if raw_cwd else None

    return OpenHookEvent(
        openhook="0.1",
        id=str(uuid.uuid4()),
        source=source,
        type=event_type,
        time=now,
        session_id=session_id,
        data=data,
        context=context,
        extensions={"legacy_payload": payload},
    )


def is_openhook(payload: dict[str, Any]) -> bool:
    """Check if a payload is an OpenHook envelope."""
    return "openhook" in payload
