/**
 * Bridge utilities for Agent Trace (https://agent-trace.dev/) integration.
 *
 * Agent Trace is an open specification for tracking AI-generated code.
 * This module converts OpenHook file.write events into Agent Trace TraceRecords.
 *
 * @example
 * ```typescript
 * import { parseStdin, toTraceRecord } from '@openhook/sdk';
 *
 * const event = await parseStdin();
 * const record = toTraceRecord(event);
 * if (record) console.log(JSON.stringify(record));
 * ```
 */

import { OpenHookEvent } from "../envelope.js";
import { EventType } from "../events.js";

export interface AgentTraceContributor {
  type: "human" | "ai" | "mixed" | "unknown";
  model?: string;
}

export interface AgentTraceConversation {
  contributor: AgentTraceContributor;
  ranges?: Array<{ start_line: number; end_line: number }>;
}

export interface AgentTraceFile {
  path: string;
  conversations: AgentTraceConversation[];
}

export interface AgentTraceRecord {
  version: string;
  id: string;
  timestamp: string;
  files: AgentTraceFile[];
  tool?: {
    name: string;
    session_id?: string;
  };
}

/**
 * Convert a file.write OpenHook event to an Agent Trace TraceRecord.
 *
 * Returns null if the event is not a file.write event or lacks a path.
 * See https://agent-trace.dev/ for the full TraceRecord specification.
 */
export function toTraceRecord(event: OpenHookEvent): AgentTraceRecord | null {
  if (event.type !== EventType.FileWrite) return null;

  const path = event.data["path"] as string | undefined;
  if (!path) return null;

  const model = event.data["model"] as string | undefined;
  const contributor: AgentTraceContributor = { type: "ai" };
  if (model) contributor.model = model;

  const conversation: AgentTraceConversation = { contributor };
  const startLine = event.data["start_line"] as number | undefined;
  const endLine = event.data["end_line"] as number | undefined;
  if (startLine && endLine) {
    conversation.ranges = [{ start_line: startLine, end_line: endLine }];
  }

  return {
    version: "0.1.0",
    id: crypto.randomUUID(),
    timestamp: event.time,
    files: [{ path, conversations: [conversation] }],
    tool: {
      name: event.source,
      session_id: event.sessionId,
    },
  };
}
