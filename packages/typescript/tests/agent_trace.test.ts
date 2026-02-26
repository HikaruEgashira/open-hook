/**
 * Agent Trace ブリッジの振る舞いを検証する仕様テスト。
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { OpenHookEvent } from "../src/envelope.js";
import { EventType } from "../src/events.js";
import { toTraceRecord } from "../src/integrations/agentTrace.js";

function makeFileWrite(dataOverrides: Record<string, unknown> = {}): OpenHookEvent {
  return new OpenHookEvent({
    source: "claude-code",
    type: EventType.FileWrite,
    sessionId: "sess_123",
    data: { path: "src/app.ts", operation: "create", ...dataOverrides },
  });
}

// ---------------------------------------------------------------------------
// file.write 以外のイベント
// ---------------------------------------------------------------------------

describe("toTraceRecord()", () => {
  describe("file.write以外のイベントの場合", () => {
    it("session.endはnullを返す", () => {
      const e = new OpenHookEvent({
        source: "claude-code",
        type: EventType.SessionEnd,
        sessionId: "s1",
      });
      assert.equal(toTraceRecord(e), null);
    });

    it("tool.endはnullを返す", () => {
      const e = new OpenHookEvent({
        source: "claude-code",
        type: EventType.ToolEnd,
        sessionId: "s1",
        data: { tool_name: "Write", status: "success" },
      });
      assert.equal(toTraceRecord(e), null);
    });

    it("tool.startはnullを返す", () => {
      const e = new OpenHookEvent({
        source: "claude-code",
        type: EventType.ToolStart,
        sessionId: "s1",
        data: { tool_name: "Write" },
      });
      assert.equal(toTraceRecord(e), null);
    });
  });

  // ---------------------------------------------------------------------------
  // path がない場合
  // ---------------------------------------------------------------------------

  describe("dataにpathが含まれない場合", () => {
    it("pathフィールドがないとnullを返す", () => {
      const e = new OpenHookEvent({
        source: "claude-code",
        type: EventType.FileWrite,
        sessionId: "s1",
        data: { operation: "create" },
      });
      assert.equal(toTraceRecord(e), null);
    });

    it("dataが空でもnullを返す", () => {
      const e = new OpenHookEvent({
        source: "claude-code",
        type: EventType.FileWrite,
        sessionId: "s1",
      });
      assert.equal(toTraceRecord(e), null);
    });
  });

  // ---------------------------------------------------------------------------
  // TraceRecord 生成
  // ---------------------------------------------------------------------------

  describe("pathを持つfile.writeイベントの場合", () => {
    describe("スキーマ準拠", () => {
      it("versionが0.1.0になる", () => {
        const record = toTraceRecord(makeFileWrite());
        assert.ok(record);
        assert.equal(record.version, "0.1.0");
      });

      it("idはUUID形式になる", () => {
        const record = toTraceRecord(makeFileWrite());
        assert.ok(record);
        assert.equal(record.id.length, 36);
      });

      it("timestampにイベントのtimeが設定される", () => {
        const event = makeFileWrite();
        const record = toTraceRecord(event);
        assert.ok(record);
        assert.equal(record.timestamp, event.time);
      });

      it("filesに1件のファイルが含まれる", () => {
        const record = toTraceRecord(makeFileWrite());
        assert.ok(record);
        assert.equal(record.files.length, 1);
      });
    });

    describe("ファイルの帰属情報", () => {
      it("filesにpathが設定される", () => {
        const record = toTraceRecord(makeFileWrite({ path: "src/utils.ts" }));
        assert.ok(record);
        assert.equal(record.files[0].path, "src/utils.ts");
      });

      it("contributor.typeはaiになる", () => {
        const record = toTraceRecord(makeFileWrite());
        assert.ok(record);
        assert.equal(record.files[0].conversations[0].contributor.type, "ai");
      });
    });

    describe("行番号が指定されている場合", () => {
      it("rangesにstart_lineとend_lineが設定される", () => {
        const record = toTraceRecord(makeFileWrite({ start_line: 1, end_line: 50 }));
        assert.ok(record);
        assert.deepEqual(
          record.files[0].conversations[0].ranges,
          [{ start_line: 1, end_line: 50 }]
        );
      });

      it("start_lineのみではrangesが設定されない", () => {
        const record = toTraceRecord(makeFileWrite({ start_line: 1 }));
        assert.ok(record);
        assert.equal(record.files[0].conversations[0].ranges, undefined);
      });
    });

    describe("行番号が指定されていない場合", () => {
      it("rangesフィールドが省略される", () => {
        const record = toTraceRecord(makeFileWrite());
        assert.ok(record);
        assert.equal(record.files[0].conversations[0].ranges, undefined);
      });
    });

    describe("modelが指定されている場合", () => {
      it("contributor.modelにmodelが設定される", () => {
        const record = toTraceRecord(
          makeFileWrite({ model: "anthropic/claude-sonnet-4-6" })
        );
        assert.ok(record);
        assert.equal(
          record.files[0].conversations[0].contributor.model,
          "anthropic/claude-sonnet-4-6"
        );
      });

      it("models.dev規約のprovider/model-name形式を保持する", () => {
        const record = toTraceRecord(
          makeFileWrite({ model: "anthropic/claude-haiku-4-5" })
        );
        assert.ok(record);
        assert.ok(record.files[0].conversations[0].contributor.model?.includes("/"));
      });
    });

    describe("modelが指定されていない場合", () => {
      it("contributor.modelフィールドが省略される", () => {
        const record = toTraceRecord(makeFileWrite());
        assert.ok(record);
        assert.equal(
          record.files[0].conversations[0].contributor.model,
          undefined
        );
      });
    });

    describe("ツール情報", () => {
      it("tool.nameにsourceが設定される", () => {
        const record = toTraceRecord(makeFileWrite());
        assert.ok(record);
        assert.equal(record.tool?.name, "claude-code");
      });

      it("tool.session_idにsession_idが設定される", () => {
        const record = toTraceRecord(makeFileWrite());
        assert.ok(record);
        assert.equal(record.tool?.session_id, "sess_123");
      });

      it("idは呼び出しごとに異なる", () => {
        const r1 = toTraceRecord(makeFileWrite());
        const r2 = toTraceRecord(makeFileWrite());
        assert.ok(r1 && r2);
        assert.notEqual(r1.id, r2.id);
      });
    });
  });
});
