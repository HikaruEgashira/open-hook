import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  OpenHookEvent,
  EventType,
  ValidationError,
  validate,
  fromLegacy,
  isOpenhook,
} from "../src/index.js";

function makePayload(overrides: Record<string, unknown> = {}) {
  return {
    openhook: "0.1",
    id: "test-id-001",
    source: "claude-code",
    type: "session.end",
    time: "2026-02-23T10:00:00Z",
    session_id: "sess_123",
    ...overrides,
  };
}

describe("validate", () => {
  it("accepts valid minimal payload", () => {
    validate(makePayload());
  });

  it("rejects missing required field", () => {
    const p = makePayload();
    delete p["source"];
    assert.throws(() => validate(p), ValidationError);
  });

  it("rejects unknown event type", () => {
    assert.throws(() => validate(makePayload({ type: "foo.bar" })), ValidationError);
  });
});

describe("OpenHookEvent", () => {
  it("parses from object", () => {
    const e = OpenHookEvent.fromObject(makePayload());
    assert.equal(e.source, "claude-code");
    assert.equal(e.type, EventType.SessionEnd);
    assert.equal(e.sessionId, "sess_123");
  });

  it("parses from JSON", () => {
    const e = OpenHookEvent.fromJSON(JSON.stringify(makePayload()));
    assert.equal(e.openhook, "0.1");
  });

  it("roundtrips", () => {
    const original = makePayload({
      data: { transcript_path: "/tmp/t.jsonl" },
      cwd: "/home",
    });
    const e = OpenHookEvent.fromObject(original);
    const restored = OpenHookEvent.fromObject(e.toObject());
    assert.equal(e.source, restored.source);
    assert.equal(e.sessionId, restored.sessionId);
    assert.equal(e.transcriptPath, restored.transcriptPath);
  });

  it("exposes transcriptPath", () => {
    const e = OpenHookEvent.fromObject(
      makePayload({ data: { transcript_path: "/tmp/sess.jsonl" } })
    );
    assert.equal(e.transcriptPath, "/tmp/sess.jsonl");
    assert.equal(e.isTrace, true);
  });

  it("returns undefined for missing transcriptPath", () => {
    const e = OpenHookEvent.fromObject(makePayload());
    assert.equal(e.transcriptPath, undefined);
    assert.equal(e.isTrace, false);
  });

  it("isMetric for countable events", () => {
    for (const t of ["session.end", "prompt.submit", "tool.start", "tool.end"]) {
      const e = OpenHookEvent.fromObject(makePayload({ type: t }));
      assert.equal(e.isMetric, true);
    }
    const e = OpenHookEvent.fromObject(makePayload({ type: "session.start" }));
    assert.equal(e.isMetric, false);
  });

  it("creates with defaults", () => {
    const e = new OpenHookEvent({
      source: "my-tool",
      type: EventType.SessionEnd,
      sessionId: "s1",
      data: { reason: "completed" },
    });
    assert.equal(e.openhook, "0.1");
    assert.equal(e.source, "my-tool");
    assert.equal(e.id.length, 36);
  });

  it("preserves extensions", () => {
    const e = OpenHookEvent.fromObject(
      makePayload({ extensions: { vendor_key: "value" } })
    );
    assert.equal(e.extensions["vendor_key"], "value");
    const obj = e.toObject();
    assert.deepEqual(obj["extensions"], { vendor_key: "value" });
  });
});

describe("compat", () => {
  it("detects openhook payload", () => {
    assert.equal(isOpenhook({ openhook: "0.1" }), true);
    assert.equal(isOpenhook({ sessionId: "abc" }), false);
  });

  it("converts claude legacy payload", () => {
    const e = fromLegacy({
      sessionId: "sess_abc",
      transcriptPath: "/home/.claude/sess.jsonl",
    });
    assert.equal(e.sessionId, "sess_abc");
    assert.equal(e.type, EventType.SessionEnd);
    assert.equal(e.transcriptPath, "/home/.claude/sess.jsonl");
  });

  it("converts cursor legacy payload", () => {
    const e = fromLegacy({ conversation_id: "conv_123" });
    assert.equal(e.source, "cursor");
    assert.equal(e.sessionId, "conv_123");
  });

  it("converts copilot tool.end", () => {
    const e = fromLegacy({
      hook_event_name: "postToolUse",
      session_id: "gh_sess",
      tool_name: "Bash",
    });
    assert.equal(e.type, EventType.ToolEnd);
    assert.equal(e.data["tool_name"], "Bash");
  });
});
