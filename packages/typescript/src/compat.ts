import { randomUUID } from "node:crypto";
import { OpenHookEvent } from "./envelope.js";
import { EventType, type EventTypeValue } from "./events.js";

const METRIC_EVENT_MAP: Record<string, EventTypeValue> = {
  userPromptSubmitted: EventType.PromptSubmit,
  userPromptSubmit: EventType.PromptSubmit,
  preToolUse: EventType.ToolStart,
  postToolUse: EventType.ToolEnd,
  sessionEnd: EventType.SessionEnd,
  stop: EventType.SessionEnd,
};

const SESSION_ID_KEYS = [
  "sessionId",
  "session_id",
  "conversation_id",
  "taskId",
  "thread-id",
];

const TRANSCRIPT_KEYS = ["transcriptPath", "transcript_path"];

function detectSource(payload: Record<string, unknown>): string {
  if (payload["source_tool"]) return String(payload["source_tool"]);
  if ("conversation_id" in payload) return "cursor";
  if ("taskId" in payload) return "cline";
  if ("thread-id" in payload) return "codex";
  if ("hook_event_name" in payload) return "copilot";
  return "unknown";
}

function extractSessionId(payload: Record<string, unknown>): string {
  for (const key of SESSION_ID_KEYS) {
    if (key in payload) return String(payload[key]);
  }
  const session = payload["session"];
  if (session && typeof session === "object" && "id" in session) {
    return String((session as Record<string, unknown>)["id"]);
  }
  return "";
}

function extractTranscriptPath(
  payload: Record<string, unknown>
): string | undefined {
  for (const key of TRANSCRIPT_KEYS) {
    if (key in payload) return String(payload[key]);
  }
  const transcript = payload["transcript"];
  if (transcript && typeof transcript === "object" && "path" in transcript) {
    return String((transcript as Record<string, unknown>)["path"]);
  }
  return undefined;
}

export function fromLegacy(payload: Record<string, unknown>): OpenHookEvent {
  const source = detectSource(payload);
  const sessionId = extractSessionId(payload);
  const hookEvent = String(payload["hook_event_name"] ?? "");
  const eventType = METRIC_EVENT_MAP[hookEvent] ?? EventType.SessionEnd;

  const data: Record<string, unknown> = {};
  const transcript = extractTranscriptPath(payload);
  if (transcript) data["transcript_path"] = transcript;
  if (eventType === EventType.ToolStart || eventType === EventType.ToolEnd) {
    if (payload["tool_name"]) data["tool_name"] = payload["tool_name"];
  }

  return new OpenHookEvent({
    source,
    type: eventType,
    sessionId,
    data,
    cwd: payload["cwd"] as string | undefined,
    extensions: { legacy_payload: payload },
    id: randomUUID(),
    time: new Date().toISOString(),
  });
}

export function isOpenhook(payload: Record<string, unknown>): boolean {
  return "openhook" in payload;
}
