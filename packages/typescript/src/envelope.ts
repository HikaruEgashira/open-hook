import { randomUUID } from "node:crypto";
import { EventType, isValidEventType, type EventTypeValue } from "./events.js";

const REQUIRED_FIELDS = [
  "openhook",
  "id",
  "source",
  "type",
  "time",
  "session_id",
] as const;

export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ValidationError";
  }
}

export interface OpenHookEventInit {
  source: string;
  type: EventTypeValue;
  sessionId: string;
  data?: Record<string, unknown>;
  cwd?: string;
  extensions?: Record<string, unknown>;
  id?: string;
  time?: string;
}

export class OpenHookEvent {
  readonly openhook: string;
  readonly id: string;
  readonly source: string;
  readonly type: EventTypeValue;
  readonly time: string;
  readonly sessionId: string;
  readonly data: Record<string, unknown>;
  readonly cwd: string | undefined;
  readonly extensions: Record<string, unknown>;

  constructor(init: OpenHookEventInit) {
    this.openhook = "0.1";
    this.id = init.id ?? randomUUID();
    this.source = init.source;
    this.type = init.type;
    this.time = init.time ?? new Date().toISOString();
    this.sessionId = init.sessionId;
    this.data = init.data ?? {};
    this.cwd = init.cwd;
    this.extensions = init.extensions ?? {};
  }

  get transcriptPath(): string | undefined {
    const p = this.data["transcript_path"];
    return typeof p === "string" ? p : undefined;
  }

  get isTrace(): boolean {
    return this.transcriptPath !== undefined;
  }

  get isMetric(): boolean {
    return (
      this.type === EventType.PromptSubmit ||
      this.type === EventType.ToolStart ||
      this.type === EventType.ToolEnd ||
      this.type === EventType.SessionEnd
    );
  }

  static fromObject(d: Record<string, unknown>): OpenHookEvent {
    validate(d);
    return new OpenHookEvent({
      source: d["source"] as string,
      type: d["type"] as EventTypeValue,
      sessionId: d["session_id"] as string,
      data: (d["data"] as Record<string, unknown>) ?? {},
      cwd: d["cwd"] as string | undefined,
      extensions: (d["extensions"] as Record<string, unknown>) ?? {},
      id: d["id"] as string,
      time: d["time"] as string,
    });
  }

  static fromJSON(raw: string): OpenHookEvent {
    return OpenHookEvent.fromObject(JSON.parse(raw));
  }

  toObject(): Record<string, unknown> {
    const obj: Record<string, unknown> = {
      openhook: this.openhook,
      id: this.id,
      source: this.source,
      type: this.type,
      time: this.time,
      session_id: this.sessionId,
    };
    if (Object.keys(this.data).length > 0) obj["data"] = this.data;
    if (this.cwd) obj["cwd"] = this.cwd;
    if (Object.keys(this.extensions).length > 0)
      obj["extensions"] = this.extensions;
    return obj;
  }

  toJSON(): string {
    return JSON.stringify(this.toObject());
  }

  emit(stream: NodeJS.WritableStream = process.stdout): void {
    stream.write(this.toJSON() + "\n");
  }
}

export function validate(d: Record<string, unknown>): void {
  const missing = REQUIRED_FIELDS.filter((f) => !(f in d));
  if (missing.length > 0) {
    throw new ValidationError(
      `Missing required fields: ${missing.sort().join(", ")}`
    );
  }

  if (typeof d["openhook"] !== "string") {
    throw new ValidationError("'openhook' must be a string");
  }

  const typeVal = d["type"];
  if (typeof typeVal !== "string" || !isValidEventType(typeVal)) {
    throw new ValidationError(`Unknown event type: ${JSON.stringify(typeVal)}`);
  }
}

export async function parseStdin(): Promise<OpenHookEvent> {
  const chunks: Buffer[] = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk as Buffer);
  }
  const raw = Buffer.concat(chunks).toString("utf-8").trim();
  if (!raw) {
    throw new ValidationError("Empty stdin");
  }
  return OpenHookEvent.fromJSON(raw);
}
