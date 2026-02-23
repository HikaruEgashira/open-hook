---
title: Specification v0.1
description: The full OpenHook protocol specification.
sidebar:
  order: 2
---

## Envelope Format

All required fields:

| Field | Type | Description |
|---|---|---|
| `openhook` | `string` | Protocol version (`"MAJOR.MINOR"`) |
| `id` | `string` | Unique event ID (UUID v4 recommended) |
| `source` | `string` | Tool identifier (lowercase kebab-case) |
| `type` | `string` | Event type (dotted lowercase) |
| `time` | `string` | ISO 8601 timestamp with timezone |
| `session_id` | `string` | Session identifier |

Optional fields: `data` (object), `cwd` (string), `extensions` (object).

## Event Types

| Type | Conformance | Description |
|---|---|---|
| `session.end` | **REQUIRED** | Session ends |
| `session.start` | OPTIONAL | Session begins |
| `prompt.submit` | OPTIONAL | User submits prompt |
| `tool.start` | OPTIONAL | Tool execution begins |
| `tool.end` | OPTIONAL | Tool execution ends |

## Data Schemas

### session.end

`transcript_path`, `reason` (`user_exit` | `timeout` | `error` | `completed`), `model`, `duration_ms`, `input_tokens`, `output_tokens`

### prompt.submit

`prompt_length`

### tool.start / tool.end

`tool_name`, `tool_call_id`, `status` (`success` | `error`), `duration_ms`

All `data` fields are OPTIONAL.

## Hook Discovery

Recommended `.openhook.json` at project root:

```json
{
  "openhook": "0.1",
  "hooks": [
    {
      "command": "otel-hooks hook --provider otlp",
      "events": ["session.end"],
      "async": true
    }
  ]
}
```

## Conformance Levels

- **Level 1 (Minimal)**: Emit `session.end` with the envelope.
- **Level 2 (Observable)**: All event types + `transcript_path`.
- **Level 3 (Discoverable)**: Support `.openhook.json`.

## Versioning

- `0.x`: Breaking changes bump MINOR.
- `1.0+`: MINOR = new optional fields/events, MAJOR = breaking changes.
- Consumers MUST check `openhook` version, SHOULD handle unknown versions best-effort.

See the [full specification on GitHub](https://github.com/HikaruEgashira/open-hook/blob/main/spec/openhook-0.1.md) for complete details.
