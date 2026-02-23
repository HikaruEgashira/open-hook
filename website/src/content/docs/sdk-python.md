---
title: Python SDK
description: OpenHook SDK for Python.
---

## Installation

```bash
pip install openhook
```

## Consuming Events (Hook Side)

```python
from openhook import parse_stdin, is_openhook, from_legacy

import json, sys

payload = json.loads(sys.stdin.read())

if is_openhook(payload):
    event = OpenHookEvent.from_dict(payload)
else:
    event = from_legacy(payload)  # backward compat

print(event.source)          # "claude-code"
print(event.type)            # EventType.SESSION_END
print(event.transcript_path) # Path("/path/to/session.jsonl") or None
print(event.is_trace)        # True if transcript_path exists
```

## Producing Events (Tool Side)

```python
from openhook import OpenHookEvent, EventType

event = OpenHookEvent.create(
    source="my-tool",
    type=EventType.SESSION_END,
    session_id="sess_123",
    data={"transcript_path": "/tmp/session.jsonl", "reason": "completed"},
)

# Write to stdout for hook consumption
event.emit()

# Or serialize
json_str = event.to_json()
dict_obj = event.to_dict()
```

## Validation

```python
from openhook import validate, ValidationError

try:
    validate({"openhook": "0.1", "type": "session.end"})
except ValidationError as e:
    print(e)  # "Missing required fields: id, session_id, source, time"
```

## Legacy Compatibility

Convert payloads from tools that don't yet support OpenHook:

```python
from openhook import from_legacy

# Claude Code legacy format
event = from_legacy({"sessionId": "abc", "transcriptPath": "/t.jsonl"})
assert event.source == "unknown"  # auto-detected when possible
assert event.transcript_path is not None

# Copilot legacy format
event = from_legacy({"hook_event_name": "postToolUse", "session_id": "s1", "tool_name": "Bash"})
assert event.type == EventType.TOOL_END
```
