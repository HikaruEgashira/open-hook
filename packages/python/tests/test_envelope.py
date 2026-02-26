"""OpenHookEvent の振る舞いを検証する仕様テスト。

テスト名はそのまま仕様書の一文として読める。
pytest -v で実行すると仕様書として機能する。
"""

import json
from io import StringIO
from pathlib import Path

import pytest

from openhook import EventType, OpenHookEvent, ValidationError, validate


# ---------------------------------------------------------------------------
# フィクスチャ
# ---------------------------------------------------------------------------

def _minimal_payload(**overrides):
    """必須フィールドのみを持つ最小ペイロードを返す。"""
    base = {
        "openhook": "0.1",
        "id": "test-id-001",
        "source": "claude-code",
        "type": "session.end",
        "time": "2026-02-23T10:00:00Z",
        "session_id": "sess_123",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# validate() 関数
# ---------------------------------------------------------------------------

class TestValidate:
    """validate() は必須フィールドと型を検証する。"""

    class 有効なペイロードの場合:
        def test_エラーが発生しない(self):
            validate(_minimal_payload())

        def test_未知のフィールドがあってもエラーが発生しない(self):
            validate(_minimal_payload(extra_field="unknown"))

    class 必須フィールドが欠けている場合:
        def test_sourceがないとValidationErrorが発生する(self):
            p = _minimal_payload()
            del p["source"]
            with pytest.raises(ValidationError):
                validate(p)

        def test_idがないとValidationErrorが発生する(self):
            p = _minimal_payload()
            del p["id"]
            with pytest.raises(ValidationError):
                validate(p)

        def test_エラーメッセージに欠けているフィールド名が含まれる(self):
            p = _minimal_payload()
            del p["source"]
            with pytest.raises(ValidationError, match="source"):
                validate(p)

    class 不明なイベントタイプの場合:
        def test_ValidationErrorが発生する(self):
            with pytest.raises(ValidationError):
                validate(_minimal_payload(type="foo.bar"))

        def test_エラーメッセージにイベントタイプが含まれる(self):
            with pytest.raises(ValidationError, match="foo.bar"):
                validate(_minimal_payload(type="foo.bar"))

        def test_空文字列のイベントタイプはValidationErrorが発生する(self):
            with pytest.raises(ValidationError):
                validate(_minimal_payload(type=""))


# ---------------------------------------------------------------------------
# OpenHookEvent の生成
# ---------------------------------------------------------------------------

class TestOpenHookEvent_from_dict:
    """from_dict() はdictからイベントを生成する。"""

    def test_各フィールドが正しくマッピングされる(self):
        e = OpenHookEvent.from_dict(_minimal_payload())
        assert e.source == "claude-code"
        assert e.type == EventType.SESSION_END
        assert e.session_id == "sess_123"
        assert e.openhook == "0.1"

    def test_dataフィールドがない場合は空dictになる(self):
        e = OpenHookEvent.from_dict(_minimal_payload())
        assert e.data == {}

    def test_extensionsフィールドがない場合は空dictになる(self):
        e = OpenHookEvent.from_dict(_minimal_payload())
        assert e.extensions == {}

    def test_contextフィールドがない場合はNoneになる(self):
        e = OpenHookEvent.from_dict(_minimal_payload())
        assert e.context is None

    def test_contextフィールドがある場合は保持される(self):
        e = OpenHookEvent.from_dict(_minimal_payload(context="file:///home/user/project"))
        assert e.context == "file:///home/user/project"

    def test_file_writeイベントタイプをパースできる(self):
        e = OpenHookEvent.from_dict(_minimal_payload(type="file.write"))
        assert e.type == EventType.FILE_WRITE


class TestOpenHookEvent_from_json:
    """from_json() はJSON文字列からイベントを生成する。"""

    def test_有効なJSON文字列からイベントを生成できる(self):
        e = OpenHookEvent.from_json(json.dumps(_minimal_payload()))
        assert e.openhook == "0.1"

    def test_不正なJSONは例外が発生する(self):
        with pytest.raises(Exception):
            OpenHookEvent.from_json("not-json")


class TestOpenHookEvent_create:
    """create() はキーワード引数でイベントを生成し、省略値を自動設定する。"""

    def test_idを省略するとUUID形式のidが自動設定される(self):
        e = OpenHookEvent.create(
            source="my-tool", type=EventType.SESSION_END, session_id="s1"
        )
        assert len(e.id) == 36  # UUID v4 形式
        assert e.id[8] == "-"

    def test_timeを省略するとISO8601形式のtimeが自動設定される(self):
        e = OpenHookEvent.create(
            source="my-tool", type=EventType.SESSION_END, session_id="s1"
        )
        assert "T" in e.time  # ISO 8601 形式

    def test_openhookフィールドは常に0_1になる(self):
        e = OpenHookEvent.create(
            source="my-tool", type=EventType.SESSION_END, session_id="s1"
        )
        assert e.openhook == "0.1"

    def test_dataを指定するとdataが設定される(self):
        e = OpenHookEvent.create(
            source="my-tool",
            type=EventType.SESSION_END,
            session_id="s1",
            data={"reason": "completed"},
        )
        assert e.data["reason"] == "completed"

    def test_idを明示指定すると自動生成されない(self):
        e = OpenHookEvent.create(
            source="my-tool",
            type=EventType.SESSION_END,
            session_id="s1",
            event_id="fixed-id",
        )
        assert e.id == "fixed-id"


# ---------------------------------------------------------------------------
# プロパティ
# ---------------------------------------------------------------------------

class TestOpenHookEvent_transcript_path:
    """transcript_path プロパティはセッションのトランスクリプトパスを返す。"""

    def test_dataにtranscript_pathがある場合はPathオブジェクトを返す(self):
        e = OpenHookEvent.from_dict(
            _minimal_payload(data={"transcript_path": "/tmp/sess.jsonl"})
        )
        assert e.transcript_path == Path("/tmp/sess.jsonl")

    def test_dataにtranscript_pathがない場合はNoneを返す(self):
        e = OpenHookEvent.from_dict(_minimal_payload())
        assert e.transcript_path is None


class TestOpenHookEvent_is_trace:
    """is_trace プロパティはtranscriptを持つイベントかどうかを返す。"""

    def test_transcript_pathがある場合はTrueを返す(self):
        e = OpenHookEvent.from_dict(
            _minimal_payload(data={"transcript_path": "/tmp/t.jsonl"})
        )
        assert e.is_trace is True

    def test_transcript_pathがない場合はFalseを返す(self):
        e = OpenHookEvent.from_dict(_minimal_payload())
        assert e.is_trace is False


class TestOpenHookEvent_is_metric:
    """is_metric プロパティは計測対象のイベントかどうかを返す。"""

    class 計測対象のイベントタイプ:
        def test_session_endはTrueを返す(self):
            e = OpenHookEvent.from_dict(_minimal_payload(type="session.end"))
            assert e.is_metric is True

        def test_tool_startはTrueを返す(self):
            e = OpenHookEvent.from_dict(_minimal_payload(type="tool.start"))
            assert e.is_metric is True

        def test_tool_endはTrueを返す(self):
            e = OpenHookEvent.from_dict(_minimal_payload(type="tool.end"))
            assert e.is_metric is True

        def test_prompt_submitはTrueを返す(self):
            e = OpenHookEvent.from_dict(_minimal_payload(type="prompt.submit"))
            assert e.is_metric is True

    class 計測対象外のイベントタイプ:
        def test_session_startはFalseを返す(self):
            e = OpenHookEvent.from_dict(_minimal_payload(type="session.start"))
            assert e.is_metric is False


# ---------------------------------------------------------------------------
# シリアライズ
# ---------------------------------------------------------------------------

class TestOpenHookEvent_to_dict:
    """to_dict() は必要なフィールドを含むdictを返す。"""

    def test_openhookフィールドが含まれる(self):
        e = OpenHookEvent.from_dict(_minimal_payload())
        assert "openhook" in e.to_dict()

    def test_dataが空の場合はto_dictに含まれない(self):
        e = OpenHookEvent.from_dict(_minimal_payload())
        assert "data" not in e.to_dict()

    def test_extensionsが空の場合はto_dictに含まれない(self):
        e = OpenHookEvent.from_dict(_minimal_payload())
        assert "extensions" not in e.to_dict()

    def test_contextがNoneの場合はto_dictに含まれない(self):
        e = OpenHookEvent.from_dict(_minimal_payload())
        assert "context" not in e.to_dict()

    def test_contextがある場合はto_dictに含まれる(self):
        e = OpenHookEvent.from_dict(_minimal_payload(context="file:///home"))
        assert e.to_dict()["context"] == "file:///home"

    def test_extensionsが設定されている場合はto_dictに含まれる(self):
        e = OpenHookEvent.from_dict(_minimal_payload(extensions={"key": "val"}))
        assert e.to_dict()["extensions"] == {"key": "val"}


class TestOpenHookEvent_ラウンドトリップ:
    """from_dict → to_dict が元のデータを忠実に復元する。"""

    def test_dataとcontextを含むペイロードが復元できる(self):
        original = _minimal_payload(
            data={"transcript_path": "/tmp/t.jsonl"},
            context="file:///home",
        )
        e = OpenHookEvent.from_dict(original)
        restored = OpenHookEvent.from_dict(e.to_dict())
        assert e == restored

    def test_extensionsを含むペイロードが復元できる(self):
        original = _minimal_payload(extensions={"vendor": "data"})
        e = OpenHookEvent.from_dict(original)
        restored = OpenHookEvent.from_dict(e.to_dict())
        assert e == restored


# ---------------------------------------------------------------------------
# emit()
# ---------------------------------------------------------------------------

class TestOpenHookEvent_emit:
    """emit() はイベントをJSON改行付きで書き出す。"""

    def test_JSON形式で書き出される(self):
        e = OpenHookEvent.create(
            source="test", type=EventType.SESSION_END, session_id="s1"
        )
        buf = StringIO()
        e.emit(file=buf)
        parsed = json.loads(buf.getvalue())
        assert parsed["source"] == "test"

    def test_末尾に改行が付く(self):
        e = OpenHookEvent.create(
            source="test", type=EventType.SESSION_END, session_id="s1"
        )
        buf = StringIO()
        e.emit(file=buf)
        assert buf.getvalue().endswith("\n")
