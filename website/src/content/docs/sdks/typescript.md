---
title: TypeScript SDK
description: OpenHook SDK for TypeScript/Node.js.
---

## Installation

```bash
npm install @openhook/sdk
```

## Consuming Events (Hook Side)

```typescript
import { OpenHookEvent, isOpenhook, fromLegacy } from '@openhook/sdk';

const payload = JSON.parse(await readStdin());

const event = isOpenhook(payload)
  ? OpenHookEvent.fromObject(payload)
  : fromLegacy(payload);

console.log(event.source);         // "claude-code"
console.log(event.type);           // "session.end"
console.log(event.transcriptPath); // "/path/to/session.jsonl" | undefined
console.log(event.isTrace);        // true if transcriptPath exists
```

## Producing Events (Tool Side)

```typescript
import { OpenHookEvent, EventType } from '@openhook/sdk';

const event = new OpenHookEvent({
  source: 'my-tool',
  type: EventType.SessionEnd,
  sessionId: 'sess_123',
  data: { transcript_path: '/tmp/session.jsonl', reason: 'completed' },
});

// Write to stdout
event.emit();

// Or serialize
const json = event.toJSON();
const obj = event.toObject();
```

## Validation

```typescript
import { validate, ValidationError } from '@openhook/sdk';

try {
  validate({ openhook: '0.1', type: 'session.end' });
} catch (e) {
  if (e instanceof ValidationError) {
    console.log(e.message); // "Missing required fields: id, session_id, source, time"
  }
}
```

## Legacy Compatibility

```typescript
import { fromLegacy, EventType } from '@openhook/sdk';

const event = fromLegacy({
  hook_event_name: 'postToolUse',
  session_id: 'gh_sess',
  tool_name: 'Bash',
});

console.log(event.type); // "tool.end"
console.log(event.data['tool_name']); // "Bash"
```
