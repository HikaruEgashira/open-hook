"""Tests for OpenHook envelope parsing, validation, and serialization."""

import json
from io import StringIO
from pathlib import Path

import pytest

from openhook import EventType, OpenHookEvent, ValidationError, validate


def _make_payload(**overrides):
    base = {
        "openhook": "0.1",
        "id": "test-id-001",
        "source": "claude-code",
        "type": "session.end",
        "time": "2026-02-23T10:00:00Z",
        "session_id": "sess_123",
    }
    base.update(overrides)
    return base


class TestValidate:
    def test_valid_minimal(self):
        validate(_make_payload())

    def test_missing_required_field(self):
        p = _make_payload()
        del p["source"]
        with pytest.raises(ValidationError, match="source"):
            validate(p)

    def test_unknown_event_type(self):
        with pytest.raises(ValidationError, match="Unknown event type"):
            validate(_make_payload(type="foo.bar"))


class TestOpenHookEvent:
    def test_from_dict(self):
        e = OpenHookEvent.from_dict(_make_payload())
        assert e.source == "claude-code"
        assert e.type == EventType.SESSION_END
        assert e.session_id == "sess_123"

    def test_from_json(self):
        e = OpenHookEvent.from_json(json.dumps(_make_payload()))
        assert e.openhook == "0.1"

    def test_roundtrip(self):
        original = _make_payload(data={"transcript_path": "/tmp/t.jsonl"}, cwd="/home")
        e = OpenHookEvent.from_dict(original)
        restored = OpenHookEvent.from_dict(e.to_dict())
        assert e == restored

    def test_transcript_path(self):
        e = OpenHookEvent.from_dict(
            _make_payload(data={"transcript_path": "/tmp/sess.jsonl"})
        )
        assert e.transcript_path == Path("/tmp/sess.jsonl")
        assert e.is_trace is True

    def test_no_transcript_path(self):
        e = OpenHookEvent.from_dict(_make_payload())
        assert e.transcript_path is None
        assert e.is_trace is False

    def test_is_metric(self):
        for t in ("session.end", "prompt.submit", "tool.start", "tool.end"):
            e = OpenHookEvent.from_dict(_make_payload(type=t))
            assert e.is_metric is True

        e = OpenHookEvent.from_dict(_make_payload(type="session.start"))
        assert e.is_metric is False

    def test_create(self):
        e = OpenHookEvent.create(
            source="my-tool",
            type=EventType.SESSION_END,
            session_id="s1",
            data={"reason": "completed"},
        )
        assert e.openhook == "0.1"
        assert e.source == "my-tool"
        assert len(e.id) == 36  # UUID

    def test_emit(self):
        e = OpenHookEvent.create(
            source="test", type=EventType.SESSION_END, session_id="s1"
        )
        buf = StringIO()
        e.emit(file=buf)
        parsed = json.loads(buf.getvalue())
        assert parsed["source"] == "test"

    def test_extensions_preserved(self):
        e = OpenHookEvent.from_dict(
            _make_payload(extensions={"vendor_key": "value"})
        )
        assert e.extensions["vendor_key"] == "value"
        assert e.to_dict()["extensions"] == {"vendor_key": "value"}
