"""OpenHook envelope: parse, validate, create, emit."""

from __future__ import annotations

import json
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .events import EventType

REQUIRED_FIELDS = frozenset({"openhook", "id", "source", "type", "time", "session_id"})


class ValidationError(Exception):
    pass


@dataclass(frozen=True)
class OpenHookEvent:
    openhook: str
    id: str
    source: str
    type: EventType
    time: str
    session_id: str
    data: dict[str, Any] = field(default_factory=dict)
    context: str | None = None
    extensions: dict[str, Any] = field(default_factory=dict)

    # --- Convenience accessors ---

    @property
    def transcript_path(self) -> Path | None:
        p = self.data.get("transcript_path")
        return Path(p) if p else None

    @property
    def is_trace(self) -> bool:
        return self.transcript_path is not None

    @property
    def is_metric(self) -> bool:
        return self.type in (
            EventType.PROMPT_SUBMIT,
            EventType.TOOL_START,
            EventType.TOOL_END,
            EventType.SESSION_END,
        )

    # --- Constructors ---

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> OpenHookEvent:
        validate(d)
        return cls(
            openhook=d["openhook"],
            id=d["id"],
            source=d["source"],
            type=EventType(d["type"]),
            time=d["time"],
            session_id=d["session_id"],
            data=d.get("data", {}),
            context=d.get("context"),
            extensions=d.get("extensions", {}),
        )

    @classmethod
    def from_json(cls, raw: str) -> OpenHookEvent:
        return cls.from_dict(json.loads(raw))

    @classmethod
    def create(
        cls,
        *,
        source: str,
        type: EventType,
        session_id: str,
        data: dict[str, Any] | None = None,
        context: str | None = None,
        extensions: dict[str, Any] | None = None,
        event_id: str | None = None,
        time: str | None = None,
    ) -> OpenHookEvent:
        return cls(
            openhook="0.1",
            id=event_id or str(uuid.uuid4()),
            source=source,
            type=type,
            time=time or datetime.now(timezone.utc).isoformat(),
            session_id=session_id,
            data=data or {},
            context=context,
            extensions=extensions or {},
        )

    # --- Serialization ---

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "openhook": self.openhook,
            "id": self.id,
            "source": self.source,
            "type": str(self.type),
            "time": self.time,
            "session_id": self.session_id,
        }
        if self.data:
            d["data"] = self.data
        if self.context:
            d["context"] = self.context
        if self.extensions:
            d["extensions"] = self.extensions
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def emit(self, file: Any = None) -> None:
        out = file or sys.stdout
        out.write(self.to_json())
        out.write("\n")
        out.flush()


def validate(d: dict[str, Any]) -> None:
    missing = REQUIRED_FIELDS - d.keys()
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(sorted(missing))}")

    if not isinstance(d.get("openhook"), str):
        raise ValidationError("'openhook' must be a string")

    type_val = d.get("type", "")
    try:
        EventType(type_val)
    except ValueError:
        raise ValidationError(f"Unknown event type: {type_val!r}") from None


def parse_stdin() -> OpenHookEvent:
    raw = sys.stdin.read()
    if not raw.strip():
        raise ValidationError("Empty stdin")
    return OpenHookEvent.from_json(raw)
