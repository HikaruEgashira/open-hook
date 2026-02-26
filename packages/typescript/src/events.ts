export const EventType = {
  SessionStart: "session.start",
  SessionEnd: "session.end",
  PromptSubmit: "prompt.submit",
  ToolStart: "tool.start",
  ToolEnd: "tool.end",
  FileWrite: "file.write",
} as const;

export type EventTypeValue = (typeof EventType)[keyof typeof EventType];

const ALL_EVENT_TYPES = new Set<string>(Object.values(EventType));

export function isValidEventType(value: string): value is EventTypeValue {
  return ALL_EVENT_TYPES.has(value);
}
