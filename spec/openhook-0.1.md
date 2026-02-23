# OpenHook Protocol Specification v0.1

## Abstract

OpenHook is a lightweight protocol that standardizes the JSON payload format for AI coding agent hook systems. It enables interoperability between AI coding tools (Claude Code, Cursor, Gemini CLI, GitHub Copilot, Kiro, Cline, Codex, OpenCode, etc.) and hook consumers (observability tools, custom scripts, CI integrations).

## Status

Draft — v0.1 (unstable)

## 1. Introduction

### 1.1 Problem

Each AI coding tool implements its own hook mechanism with incompatible payload formats:

- Session identifiers use different field names (`sessionId`, `conversation_id`, `taskId`, `thread-id`, etc.)
- Event types are inconsistent (`Stop`, `stop`, `SessionEnd`, `userPromptSubmitted`, etc.)
- Hook registration formats vary (JSON, TOML, shell scripts, JS plugins)

Hook consumers must implement per-tool adapters with heuristic payload detection, leading to fragile integrations that break when tools change their formats.

### 1.2 Solution

OpenHook defines a self-describing JSON envelope that all tools SHOULD send to hook processes via stdin. A single `openhook` field identifies conforming payloads, eliminating heuristic detection entirely.

### 1.3 Conventions

The key words "MUST", "MUST NOT", "SHOULD", "SHOULD NOT", "MAY", and "OPTIONAL" are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

## 2. Envelope Format

An OpenHook event is a single JSON object written to the hook process's stdin.

### 2.1 Required Fields

| Field | Type | Description |
|---|---|---|
| `openhook` | `string` | Protocol version in `MAJOR.MINOR` format (e.g., `"0.1"`). Presence of this field identifies an OpenHook envelope. |
| `id` | `string` | Unique event identifier. SHOULD be a UUID v4. Used as an idempotency key. |
| `source` | `string` | Tool identifier (e.g., `"claude-code"`, `"cursor"`, `"gemini-cli"`). MUST use lowercase kebab-case. |
| `type` | `string` | Event type from Section 3. MUST use dotted lowercase format. |
| `time` | `string` | ISO 8601 timestamp with timezone (e.g., `"2026-02-23T10:15:30.123Z"`). |
| `session_id` | `string` | Session/conversation/task identifier. Opaque string. |

### 2.2 Optional Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `data` | `object` | `{}` | Event-type-specific payload. Schema varies by `type`. |
| `cwd` | `string` | — | Working directory at time of event. |
| `extensions` | `object` | `{}` | Vendor-specific data. Consumers MUST ignore unknown keys. |

### 2.3 Example

```json
{
  "openhook": "0.1",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "source": "claude-code",
  "type": "session.end",
  "time": "2026-02-23T10:15:30.123Z",
  "session_id": "sess_abc123",
  "data": {
    "transcript_path": "/home/user/.claude/sessions/sess_abc123.jsonl"
  },
  "cwd": "/home/user/my-project"
}
```

## 3. Event Types

### 3.1 Lifecycle Events

| Type | Conformance | Description |
|---|---|---|
| `session.start` | OPTIONAL | A new coding session begins. |
| `session.end` | REQUIRED | A coding session ends. All conforming tools MUST emit this event. |
| `prompt.submit` | OPTIONAL | The user submits a prompt to the agent. |
| `tool.start` | OPTIONAL | The agent begins executing a tool (e.g., Bash, file read). |
| `tool.end` | OPTIONAL | The agent finishes executing a tool. |

Tools that support only `session.end` are fully conforming. The remaining events provide richer observability for tools that support them.

### 3.2 Data Schemas by Event Type

#### `session.start`

| Field | Type | Description |
|---|---|---|
| `model` | `string` | Model identifier (e.g., `"claude-sonnet-4-20250514"`). |

#### `session.end`

| Field | Type | Description |
|---|---|---|
| `transcript_path` | `string` | Absolute path to the session transcript file (typically JSONL). |
| `reason` | `string` | Why the session ended. One of: `"user_exit"`, `"timeout"`, `"error"`, `"completed"`. |
| `model` | `string` | Model identifier. |
| `duration_ms` | `integer` | Session duration in milliseconds. |
| `input_tokens` | `integer` | Total input tokens consumed. |
| `output_tokens` | `integer` | Total output tokens consumed. |

#### `prompt.submit`

| Field | Type | Description |
|---|---|---|
| `prompt_length` | `integer` | Character length of the prompt. |

#### `tool.start`

| Field | Type | Description |
|---|---|---|
| `tool_name` | `string` | Name of the tool being invoked. |
| `tool_call_id` | `string` | Unique identifier for this tool invocation. |

#### `tool.end`

| Field | Type | Description |
|---|---|---|
| `tool_name` | `string` | Name of the tool. |
| `tool_call_id` | `string` | Same identifier from the corresponding `tool.start`. |
| `status` | `string` | Outcome. One of: `"success"`, `"error"`. |
| `duration_ms` | `integer` | Tool execution duration in milliseconds. |

All `data` fields are OPTIONAL. Tools provide what they can.

## 4. Hook Discovery (Recommended)

Tools MAY support a project-level hook discovery file:

**`.openhook.json`** (project root):

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

| Field | Type | Default | Description |
|---|---|---|---|
| `command` | `string` | — | Shell command. Receives OpenHook JSON via stdin. REQUIRED. |
| `events` | `string[]` | `["*"]` | Event types to subscribe to. `["*"]` means all events. |
| `async` | `boolean` | `false` | If `true`, tool fires the hook without waiting for exit. |

Tools that already have their own hook configuration (e.g., Claude Code's `settings.json`) MAY continue using those mechanisms, but SHOULD emit OpenHook-conforming payloads.

## 5. Versioning

- The `openhook` field carries `MAJOR.MINOR` (no patch).
- During `0.x`: breaking changes bump MINOR.
- After `1.0`:
  - MINOR: new optional fields, new event types.
  - MAJOR: removing required fields, changing semantics.
- Consumers MUST check the `openhook` version. Unknown versions SHOULD be processed on a best-effort basis with a logged warning.
- The `extensions` object provides a forward-compatible escape hatch for vendor-specific data.

## 6. Conformance Levels

### Level 1: Minimal (REQUIRED)

- Emit `session.end` events with the OpenHook envelope.
- Include all required envelope fields.

### Level 2: Observable (RECOMMENDED)

- Level 1, plus:
- Emit `session.start`, `prompt.submit`, `tool.start`, and `tool.end` events.
- Include `data.transcript_path` on `session.end` when available.

### Level 3: Discoverable (OPTIONAL)

- Level 2, plus:
- Support `.openhook.json` hook discovery.

## 7. Security Considerations

- Hook commands execute with the user's privileges. Tools SHOULD NOT run hook commands without user consent.
- Transcript paths may contain sensitive data. Hook consumers SHOULD treat transcript contents as confidential.
- The `extensions` field MUST NOT be used to bypass security controls.

## 8. IANA Considerations

This specification does not require any IANA registrations.
