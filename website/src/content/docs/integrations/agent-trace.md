---
title: Agent Trace Integration
description: Connect OpenHook events to Agent Trace for AI code attribution.
---

[Agent Trace](https://agent-trace.dev/) is an open specification for tracking AI-generated code at the file and line level. OpenHook's `file.write` event is designed as the primary integration point.

## イベントの責務分担

| イベント | 用途 |
|---|---|
| `tool.start` / `tool.end` | 実行の可観測性（レイテンシ・エラー） |
| `file.write` | コード帰属（誰が何をどこに書いたか） |

`file.write` はファイル変更ごとに1回発行されます。`tool.start` / `tool.end` とは独立したイベントなので、Agent Trace コンシューマーは `file.write` だけを購読すれば済みます。

## `file.write` イベント

```json
{
  "openhook": "0.1",
  "type": "file.write",
  "source": "claude-code",
  "session_id": "sess_abc123",
  "time": "2026-02-23T10:15:45.678Z",
  "data": {
    "path": "src/utils.ts",
    "operation": "create",
    "start_line": 1,
    "end_line": 30,
    "model": "anthropic/claude-sonnet-4-6",
    "tool_call_id": "call_xyz789"
  }
}
```

`model` は [models.dev](https://models.dev) 規約（`provider/model-name`）に従い、Agent Trace の `contributor.model` に直接マッピングされます。

## ブリッジユーティリティ

両 SDK に `to_trace_record` / `toTraceRecord` 関数が付属しています。

### Python

```python
from openhook import parse_stdin
from openhook.integrations.agent_trace import to_trace_record
import json

event = parse_stdin()
record = to_trace_record(event)
if record:
    # git notes、.agent-trace.jsonl への追記など
    print(json.dumps(record))
```

### TypeScript

```typescript
import { parseStdin, toTraceRecord } from '@openhook/sdk';
import { appendFileSync } from 'node:fs';

const event = await parseStdin();
const record = toTraceRecord(event);
if (record) {
  appendFileSync('.agent-trace.jsonl', JSON.stringify(record) + '\n');
}
```

## フック登録

`.openhook.json` に追加します。`file.write` のみを購読し、`async: true` でブロッキングを防ぎます：

```json
{
  "openhook": "0.1",
  "hooks": [
    {
      "command": "agent-trace-hook",
      "events": ["file.write"],
      "async": true
    }
  ]
}
```

## 生成される TraceRecord

```json
{
  "version": "0.1.0",
  "id": "<uuid>",
  "timestamp": "2026-02-23T10:15:45.678Z",
  "files": [
    {
      "path": "src/utils.ts",
      "conversations": [
        {
          "contributor": {
            "type": "ai",
            "model": "anthropic/claude-sonnet-4-6"
          },
          "ranges": [{ "start_line": 1, "end_line": 30 }]
        }
      ]
    }
  ],
  "tool": {
    "name": "claude-code",
    "session_id": "sess_abc123"
  }
}
```
