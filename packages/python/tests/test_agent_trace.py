"""Agent Trace ブリッジの振る舞いを検証する仕様テスト。"""

from openhook import EventType, OpenHookEvent
from openhook.integrations.agent_trace import to_trace_record


def _make_file_write(**data_overrides) -> OpenHookEvent:
    data = {"path": "src/app.ts", "operation": "create"}
    data.update(data_overrides)
    return OpenHookEvent.create(
        source="claude-code",
        type=EventType.FILE_WRITE,
        session_id="sess_123",
        data=data,
    )


# ---------------------------------------------------------------------------
# to_trace_record()
# ---------------------------------------------------------------------------

class TestToTraceRecord_file_write以外のイベント:
    """file.write 以外のイベントは変換対象外である。"""

    def test_session_endはNoneを返す(self):
        event = OpenHookEvent.create(
            source="claude-code", type=EventType.SESSION_END, session_id="s1"
        )
        assert to_trace_record(event) is None

    def test_tool_endはNoneを返す(self):
        event = OpenHookEvent.create(
            source="claude-code",
            type=EventType.TOOL_END,
            session_id="s1",
            data={"tool_name": "Write", "status": "success"},
        )
        assert to_trace_record(event) is None

    def test_tool_startはNoneを返す(self):
        event = OpenHookEvent.create(
            source="claude-code",
            type=EventType.TOOL_START,
            session_id="s1",
            data={"tool_name": "Write"},
        )
        assert to_trace_record(event) is None


class TestToTraceRecord_pathがない場合:
    """dataにpathが含まれないfile.writeはNoneを返す。"""

    def test_pathフィールドがないとNoneを返す(self):
        event = OpenHookEvent.create(
            source="claude-code",
            type=EventType.FILE_WRITE,
            session_id="s1",
            data={"operation": "create"},
        )
        assert to_trace_record(event) is None

    def test_dataが空でもNoneを返す(self):
        event = OpenHookEvent.create(
            source="claude-code", type=EventType.FILE_WRITE, session_id="s1"
        )
        assert to_trace_record(event) is None


class TestToTraceRecord_TraceRecord生成:
    """pathを持つfile.writeはAgent Trace TraceRecordを生成する。"""

    class スキーマ準拠:
        def test_versionが0_1_0になる(self):
            record = to_trace_record(_make_file_write())
            assert record["version"] == "0.1.0"

        def test_idはUUID形式になる(self):
            record = to_trace_record(_make_file_write())
            assert len(record["id"]) == 36

        def test_timestampにイベントのtimeが設定される(self):
            event = _make_file_write()
            record = to_trace_record(event)
            assert record["timestamp"] == event.time

        def test_filesに1件のファイルが含まれる(self):
            record = to_trace_record(_make_file_write())
            assert len(record["files"]) == 1

    class ファイルの帰属情報:
        def test_filesにpathが設定される(self):
            record = to_trace_record(_make_file_write(path="src/utils.ts"))
            assert record["files"][0]["path"] == "src/utils.ts"

        def test_contributor_typeはaiになる(self):
            record = to_trace_record(_make_file_write())
            contributor = record["files"][0]["conversations"][0]["contributor"]
            assert contributor["type"] == "ai"

    class 行番号が指定されている場合:
        def test_rangesにstart_lineとend_lineが設定される(self):
            record = to_trace_record(_make_file_write(start_line=1, end_line=50))
            ranges = record["files"][0]["conversations"][0]["ranges"]
            assert ranges == [{"start_line": 1, "end_line": 50}]

        def test_start_lineのみでは行番号は設定されない(self):
            record = to_trace_record(_make_file_write(start_line=1))
            conv = record["files"][0]["conversations"][0]
            assert "ranges" not in conv

    class 行番号が指定されていない場合:
        def test_rangesフィールドが省略される(self):
            record = to_trace_record(_make_file_write())
            conv = record["files"][0]["conversations"][0]
            assert "ranges" not in conv

    class modelが指定されている場合:
        def test_contributor_modelにmodelが設定される(self):
            record = to_trace_record(_make_file_write(model="anthropic/claude-sonnet-4-6"))
            contributor = record["files"][0]["conversations"][0]["contributor"]
            assert contributor["model"] == "anthropic/claude-sonnet-4-6"

        def test_models_dev規約のprovider_model_name形式を保持する(self):
            record = to_trace_record(_make_file_write(model="anthropic/claude-haiku-4-5"))
            contributor = record["files"][0]["conversations"][0]["contributor"]
            assert "/" in contributor["model"]

    class modelが指定されていない場合:
        def test_contributor_modelフィールドが省略される(self):
            record = to_trace_record(_make_file_write())
            contributor = record["files"][0]["conversations"][0]["contributor"]
            assert "model" not in contributor

    class ツール情報:
        def test_tool_nameにsourceが設定される(self):
            record = to_trace_record(_make_file_write())
            assert record["tool"]["name"] == "claude-code"

        def test_tool_session_idにsession_idが設定される(self):
            record = to_trace_record(_make_file_write())
            assert record["tool"]["session_id"] == "sess_123"

        def test_idは呼び出しごとに異なる(self):
            r1 = to_trace_record(_make_file_write())
            r2 = to_trace_record(_make_file_write())
            assert r1["id"] != r2["id"]
