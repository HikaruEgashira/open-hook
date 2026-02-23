# OpenHook

A lightweight protocol that standardizes hook payloads for AI coding agent tools.

## Problem

Every AI coding tool (Claude Code, Cursor, Gemini CLI, GitHub Copilot, Kiro, etc.) implements its own hook format — different field names, event types, and configuration mechanisms. Hook consumers must write per-tool adapters with fragile heuristic detection.

## Solution

OpenHook defines a self-describing JSON envelope. A single `openhook` field identifies conforming payloads, eliminating heuristic detection entirely.

```json
{
  "openhook": "0.1",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "source": "claude-code",
  "type": "session.end",
  "time": "2026-02-23T10:15:30.123Z",
  "session_id": "sess_abc123",
  "data": {
    "transcript_path": "/path/to/session.jsonl"
  }
}
```

## Event Types

| Type | Required | Description |
|---|---|---|
| `session.end` | REQUIRED | Session ends. Minimum conformance. |
| `session.start` | OPTIONAL | Session begins. |
| `prompt.submit` | OPTIONAL | User submits a prompt. |
| `tool.start` | OPTIONAL | Agent starts using a tool. |
| `tool.end` | OPTIONAL | Agent finishes using a tool. |

## SDKs

### Python

```bash
pip install openhook
```

```python
from openhook import OpenHookEvent, EventType, parse_stdin

# Consume hook events
event = parse_stdin()
print(event.source, event.type, event.transcript_path)

# Produce hook events
event = OpenHookEvent.create(
    source="my-tool",
    type=EventType.SESSION_END,
    session_id="sess_123",
)
event.emit()
```

### TypeScript

```bash
npm install @openhook/sdk
```

```typescript
import { parseStdin, OpenHookEvent, EventType } from '@openhook/sdk';

const event = await parseStdin();
console.log(event.source, event.type, event.transcriptPath);
```

## Specification

See [spec/openhook-0.1.md](spec/openhook-0.1.md) for the full protocol specification.

## License

Apache-2.0
