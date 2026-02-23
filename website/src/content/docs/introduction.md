---
title: Introduction
description: Why OpenHook exists and what it solves.
sidebar:
  order: 1
---

## The Problem

Every AI coding tool implements its own hook mechanism with incompatible payload formats:

| Tool | Session ID field | Event format |
|---|---|---|
| Claude Code | `sessionId` | `Stop` |
| Cursor | `conversation_id` | `stop` |
| Gemini CLI | `session_id` + `timestamp` | `SessionEnd` |
| GitHub Copilot | `session_id` + `hook_event_name` | `userPromptSubmitted`, `postToolUse`, ... |
| Kiro | `session_id` + `hook_event_name` | `userPromptSubmit`, `stop`, ... |
| Cline | `taskId` | shell script |
| Codex | `thread-id` | TOML config |
| OpenCode | `source_tool` self-tag | JS plugin |

Hook consumers (observability tools, custom scripts) must implement per-tool adapters with fragile heuristic payload detection.

## The Solution

OpenHook defines a **self-describing JSON envelope** that all tools send to hook processes via stdin.

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

The presence of the `openhook` field is the **sole discriminator**. No heuristic detection needed.

## Design Principles

- **Minimal**: Only `session.end` is required. Tools implement what they can.
- **Self-describing**: The `openhook` + `source` fields eliminate ambiguity.
- **Extensible**: The `extensions` object allows vendor-specific data without breaking the spec.
- **Backward-compatible**: Legacy payloads can be converted via SDK compat modules.

## Getting Started

1. Read the [Specification](/open-hook/spec/) for the full protocol definition.
2. Use the [Python SDK](/open-hook/sdk-python/) or [TypeScript SDK](/open-hook/sdk-typescript/) to integrate.
