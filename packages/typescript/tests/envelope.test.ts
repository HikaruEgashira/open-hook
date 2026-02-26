/**
 * OpenHookEvent の振る舞いを検証する仕様テスト。
 * テスト名はそのまま仕様書の一文として読める。
 */
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

function minimalPayload(overrides: Record<string, unknown> = {}) {
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

// ---------------------------------------------------------------------------
// validate()
// ---------------------------------------------------------------------------

describe("validate()", () => {
  describe("有効なペイロードの場合", () => {
    it("エラーが発生しない", () => {
      assert.doesNotThrow(() => validate(minimalPayload()));
    });

    it("未知のフィールドがあってもエラーが発生しない", () => {
      assert.doesNotThrow(() => validate(minimalPayload({ extra: "field" })));
    });
  });

  describe("必須フィールドが欠けている場合", () => {
    it("sourceがないとValidationErrorが発生する", () => {
      const p = minimalPayload();
      delete p["source"];
      assert.throws(() => validate(p), ValidationError);
    });

    it("idがないとValidationErrorが発生する", () => {
      const p = minimalPayload();
      delete p["id"];
      assert.throws(() => validate(p), ValidationError);
    });

    it("エラーメッセージに欠けているフィールド名が含まれる", () => {
      const p = minimalPayload();
      delete p["source"];
      assert.throws(() => validate(p), /source/);
    });
  });

  describe("不明なイベントタイプの場合", () => {
    it("ValidationErrorが発生する", () => {
      assert.throws(() => validate(minimalPayload({ type: "foo.bar" })), ValidationError);
    });

    it("エラーメッセージにイベントタイプが含まれる", () => {
      assert.throws(() => validate(minimalPayload({ type: "foo.bar" })), /foo\.bar/);
    });

    it("空文字列のイベントタイプはValidationErrorが発生する", () => {
      assert.throws(() => validate(minimalPayload({ type: "" })), ValidationError);
    });
  });
});

// ---------------------------------------------------------------------------
// OpenHookEvent の生成
// ---------------------------------------------------------------------------

describe("OpenHookEvent.fromObject()", () => {
  describe("有効なペイロードの場合", () => {
    it("各フィールドが正しくマッピングされる", () => {
      const e = OpenHookEvent.fromObject(minimalPayload());
      assert.equal(e.source, "claude-code");
      assert.equal(e.type, EventType.SessionEnd);
      assert.equal(e.sessionId, "sess_123");
    });

    it("dataフィールドがない場合は空objectになる", () => {
      const e = OpenHookEvent.fromObject(minimalPayload());
      assert.deepEqual(e.data, {});
    });

    it("extensionsフィールドがない場合は空objectになる", () => {
      const e = OpenHookEvent.fromObject(minimalPayload());
      assert.deepEqual(e.extensions, {});
    });

    it("contextフィールドがない場合はundefinedになる", () => {
      const e = OpenHookEvent.fromObject(minimalPayload());
      assert.equal(e.context, undefined);
    });

    it("contextフィールドがある場合は保持される", () => {
      const e = OpenHookEvent.fromObject(
        minimalPayload({ context: "file:///home/user/project" })
      );
      assert.equal(e.context, "file:///home/user/project");
    });

    it("file.writeイベントタイプをパースできる", () => {
      const e = OpenHookEvent.fromObject(minimalPayload({ type: "file.write" }));
      assert.equal(e.type, EventType.FileWrite);
    });
  });
});

describe("OpenHookEvent.fromJSON()", () => {
  it("有効なJSON文字列からイベントを生成できる", () => {
    const e = OpenHookEvent.fromJSON(JSON.stringify(minimalPayload()));
    assert.equal(e.openhook, "0.1");
  });

  it("不正なJSONは例外が発生する", () => {
    assert.throws(() => OpenHookEvent.fromJSON("not-json"));
  });
});

describe("new OpenHookEvent()", () => {
  describe("省略値の自動設定", () => {
    it("idを省略するとUUID形式のidが自動設定される", () => {
      const e = new OpenHookEvent({
        source: "my-tool",
        type: EventType.SessionEnd,
        sessionId: "s1",
      });
      assert.equal(e.id.length, 36);
      assert.equal(e.id[8], "-");
    });

    it("timeを省略するとISO8601形式のtimeが自動設定される", () => {
      const e = new OpenHookEvent({
        source: "my-tool",
        type: EventType.SessionEnd,
        sessionId: "s1",
      });
      assert.ok(e.time.includes("T"));
    });

    it("openhookフィールドは常に0.1になる", () => {
      const e = new OpenHookEvent({
        source: "my-tool",
        type: EventType.SessionEnd,
        sessionId: "s1",
      });
      assert.equal(e.openhook, "0.1");
    });
  });
});

// ---------------------------------------------------------------------------
// プロパティ
// ---------------------------------------------------------------------------

describe("transcriptPath プロパティ", () => {
  it("dataにtranscript_pathがある場合はその値を返す", () => {
    const e = OpenHookEvent.fromObject(
      minimalPayload({ data: { transcript_path: "/tmp/sess.jsonl" } })
    );
    assert.equal(e.transcriptPath, "/tmp/sess.jsonl");
  });

  it("dataにtranscript_pathがない場合はundefinedを返す", () => {
    const e = OpenHookEvent.fromObject(minimalPayload());
    assert.equal(e.transcriptPath, undefined);
  });
});

describe("isTrace プロパティ", () => {
  it("transcript_pathがある場合はtrueを返す", () => {
    const e = OpenHookEvent.fromObject(
      minimalPayload({ data: { transcript_path: "/tmp/t.jsonl" } })
    );
    assert.equal(e.isTrace, true);
  });

  it("transcript_pathがない場合はfalseを返す", () => {
    const e = OpenHookEvent.fromObject(minimalPayload());
    assert.equal(e.isTrace, false);
  });
});

describe("isMetric プロパティ", () => {
  describe("計測対象のイベントタイプ", () => {
    for (const type of ["session.end", "tool.start", "tool.end", "prompt.submit"]) {
      it(`${type}はtrueを返す`, () => {
        const e = OpenHookEvent.fromObject(minimalPayload({ type }));
        assert.equal(e.isMetric, true);
      });
    }
  });

  describe("計測対象外のイベントタイプ", () => {
    it("session.startはfalseを返す", () => {
      const e = OpenHookEvent.fromObject(minimalPayload({ type: "session.start" }));
      assert.equal(e.isMetric, false);
    });
  });
});

// ---------------------------------------------------------------------------
// シリアライズ
// ---------------------------------------------------------------------------

describe("toObject()", () => {
  it("dataが空の場合はtoObjectに含まれない", () => {
    const e = OpenHookEvent.fromObject(minimalPayload());
    assert.ok(!("data" in e.toObject()));
  });

  it("extensionsが空の場合はtoObjectに含まれない", () => {
    const e = OpenHookEvent.fromObject(minimalPayload());
    assert.ok(!("extensions" in e.toObject()));
  });

  it("contextがundefinedの場合はtoObjectに含まれない", () => {
    const e = OpenHookEvent.fromObject(minimalPayload());
    assert.ok(!("context" in e.toObject()));
  });

  it("contextがある場合はtoObjectに含まれる", () => {
    const e = OpenHookEvent.fromObject(
      minimalPayload({ context: "file:///home" })
    );
    assert.equal(e.toObject()["context"], "file:///home");
  });

  it("extensionsが設定されている場合はtoObjectに含まれる", () => {
    const e = OpenHookEvent.fromObject(
      minimalPayload({ extensions: { key: "val" } })
    );
    assert.deepEqual(e.toObject()["extensions"], { key: "val" });
  });
});

describe("ラウンドトリップ（fromObject → toObject）", () => {
  it("dataとcontextを含むペイロードが復元できる", () => {
    const original = minimalPayload({
      data: { transcript_path: "/tmp/t.jsonl" },
      context: "file:///home",
    });
    const e = OpenHookEvent.fromObject(original);
    const restored = OpenHookEvent.fromObject(e.toObject());
    assert.equal(e.source, restored.source);
    assert.equal(e.sessionId, restored.sessionId);
    assert.equal(e.transcriptPath, restored.transcriptPath);
    assert.equal(e.context, restored.context);
  });
});

// ---------------------------------------------------------------------------
// compat
// ---------------------------------------------------------------------------

describe("isOpenhook()", () => {
  it("openhookフィールドが存在する場合はtrueを返す", () => {
    assert.equal(isOpenhook({ openhook: "0.1" }), true);
  });

  it("openhookフィールドが存在しない場合はfalseを返す", () => {
    assert.equal(isOpenhook({ sessionId: "abc" }), false);
  });

  it("空のオブジェクトはfalseを返す", () => {
    assert.equal(isOpenhook({}), false);
  });
});

describe("fromLegacy()", () => {
  describe("ソース検出", () => {
    it("conversation_idを持つペイロードはcursorと判定される", () => {
      const e = fromLegacy({ conversation_id: "conv_123" });
      assert.equal(e.source, "cursor");
      assert.equal(e.sessionId, "conv_123");
    });

    it("taskIdを持つペイロードはclineと判定される", () => {
      const e = fromLegacy({ taskId: "task_xyz" });
      assert.equal(e.source, "cline");
    });

    it("hook_event_nameを持つペイロードはcopilotと判定される", () => {
      const e = fromLegacy({ hook_event_name: "postToolUse", session_id: "s1" });
      assert.equal(e.source, "copilot");
    });
  });

  describe("イベントタイプ変換", () => {
    it("postToolUseはtool.endに変換される", () => {
      const e = fromLegacy({ hook_event_name: "postToolUse", session_id: "s1" });
      assert.equal(e.type, EventType.ToolEnd);
    });

    it("preToolUseはtool.startに変換される", () => {
      const e = fromLegacy({ hook_event_name: "preToolUse", session_id: "s1" });
      assert.equal(e.type, EventType.ToolStart);
    });

    it("userPromptSubmittedはprompt.submitに変換される", () => {
      const e = fromLegacy({ hook_event_name: "userPromptSubmitted", session_id: "s1" });
      assert.equal(e.type, EventType.PromptSubmit);
    });
  });

  describe("context変換（cwd → file:// URI）", () => {
    it("絶対パスはfile://URIに変換される", () => {
      const e = fromLegacy({ sessionId: "s1", cwd: "/home/user/project" });
      assert.equal(e.context, "file:///home/user/project");
    });

    it("既にfile://URIの場合はそのまま保持される", () => {
      const e = fromLegacy({ sessionId: "s1", cwd: "file:///home/user/project" });
      assert.equal(e.context, "file:///home/user/project");
    });

    it("cwdがない場合はcontextがundefinedになる", () => {
      const e = fromLegacy({ sessionId: "s1" });
      assert.equal(e.context, undefined);
    });
  });

  describe("データ保全", () => {
    it("元のペイロードがextensions.legacy_payloadに保存される", () => {
      const payload = { sessionId: "s1" };
      const e = fromLegacy(payload);
      assert.deepEqual(e.extensions["legacy_payload"], payload);
    });

    it("tool_nameはdataに移される", () => {
      const e = fromLegacy({
        hook_event_name: "postToolUse",
        session_id: "s1",
        tool_name: "Bash",
      });
      assert.equal(e.data["tool_name"], "Bash");
    });
  });
});
