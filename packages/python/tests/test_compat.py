"""レガシーペイロード変換の振る舞いを検証する仕様テスト。"""

from openhook import EventType, from_legacy, is_openhook


# ---------------------------------------------------------------------------
# is_openhook()
# ---------------------------------------------------------------------------

class TestIsOpenhook:
    """is_openhook() はペイロードがOpenHook形式かどうかを判定する。"""

    class openhookフィールドが存在する場合:
        def test_Trueを返す(self):
            assert is_openhook({"openhook": "0.1"}) is True

        def test_他のフィールドがなくてもTrueを返す(self):
            assert is_openhook({"openhook": "0.1"}) is True

    class openhookフィールドが存在しない場合:
        def test_Falseを返す(self):
            assert is_openhook({"sessionId": "abc"}) is False

        def test_空のdictはFalseを返す(self):
            assert is_openhook({}) is False


# ---------------------------------------------------------------------------
# from_legacy() — ソース検出
# ---------------------------------------------------------------------------

class TestFromLegacy_ソース検出:
    """from_legacy() は既知のフィールドからツールソースを検出する。"""

    def test_sessionIdとtranscriptPathを持つペイロードはclaude_codeと判定される(self):
        e = from_legacy({"sessionId": "s1", "transcriptPath": "/t.jsonl"})
        assert e.source == "claude-code"

    def test_conversation_idを持つペイロードはcursorと判定される(self):
        e = from_legacy({"conversation_id": "conv_123"})
        assert e.source == "cursor"

    def test_taskIdを持つペイロードはclineと判定される(self):
        e = from_legacy({"taskId": "task_xyz"})
        assert e.source == "cline"

    def test_thread_idを持つペイロードはcodexと判定される(self):
        e = from_legacy({"thread-id": "t-001"})
        assert e.source == "codex"

    def test_hook_event_nameを持つペイロードはcopilotと判定される(self):
        e = from_legacy({"hook_event_name": "postToolUse", "session_id": "s1"})
        assert e.source == "copilot"

    def test_未知のペイロードはunknownと判定される(self):
        e = from_legacy({"unknown_field": "value"})
        assert e.source == "unknown"


# ---------------------------------------------------------------------------
# from_legacy() — イベントタイプ変換
# ---------------------------------------------------------------------------

class TestFromLegacy_イベントタイプ変換:
    """from_legacy() はhook_event_nameを標準イベントタイプに変換する。"""

    def test_preToolUseはtool_startに変換される(self):
        e = from_legacy({"hook_event_name": "preToolUse", "session_id": "s1"})
        assert e.type == EventType.TOOL_START

    def test_postToolUseはtool_endに変換される(self):
        e = from_legacy({"hook_event_name": "postToolUse", "session_id": "s1"})
        assert e.type == EventType.TOOL_END

    def test_userPromptSubmittedはprompt_submitに変換される(self):
        e = from_legacy({"hook_event_name": "userPromptSubmitted", "session_id": "s1"})
        assert e.type == EventType.PROMPT_SUBMIT

    def test_userPromptSubmitはprompt_submitに変換される(self):
        e = from_legacy({"hook_event_name": "userPromptSubmit", "session_id": "s1"})
        assert e.type == EventType.PROMPT_SUBMIT

    def test_sessionEndはsession_endに変換される(self):
        e = from_legacy({"hook_event_name": "sessionEnd", "session_id": "s1"})
        assert e.type == EventType.SESSION_END

    def test_stopはsession_endに変換される(self):
        e = from_legacy({"hook_event_name": "stop", "session_id": "s1"})
        assert e.type == EventType.SESSION_END

    def test_未知のhook_event_nameはsession_endにフォールバックされる(self):
        e = from_legacy({"hook_event_name": "unknownEvent", "session_id": "s1"})
        assert e.type == EventType.SESSION_END


# ---------------------------------------------------------------------------
# from_legacy() — セッションID抽出
# ---------------------------------------------------------------------------

class TestFromLegacy_セッションID抽出:
    """from_legacy() は複数の命名規則からセッションIDを抽出する。"""

    def test_sessionIdフィールドからセッションIDを取得する(self):
        e = from_legacy({"sessionId": "sess_abc"})
        assert e.session_id == "sess_abc"

    def test_session_idフィールドからセッションIDを取得する(self):
        e = from_legacy({"session_id": "sess_abc"})
        assert e.session_id == "sess_abc"

    def test_conversation_idフィールドからセッションIDを取得する(self):
        e = from_legacy({"conversation_id": "conv_123"})
        assert e.session_id == "conv_123"

    def test_taskIdフィールドからセッションIDを取得する(self):
        e = from_legacy({"taskId": "task_xyz"})
        assert e.session_id == "task_xyz"


# ---------------------------------------------------------------------------
# from_legacy() — context変換（cwd → file:// URI）
# ---------------------------------------------------------------------------

class TestFromLegacy_context変換:
    """from_legacy() はレガシーのcwdパスをfile:// URIに昇格させる。"""

    def test_絶対パスはfile_URIに変換される(self):
        e = from_legacy({"sessionId": "s1", "cwd": "/home/user/project"})
        assert e.context == "file:///home/user/project"

    def test_既にfile_URIの場合はそのまま保持される(self):
        e = from_legacy({"sessionId": "s1", "cwd": "file:///home/user/project"})
        assert e.context == "file:///home/user/project"

    def test_https_URIの場合はそのまま保持される(self):
        e = from_legacy({"sessionId": "s1", "cwd": "https://example.com/page"})
        assert e.context == "https://example.com/page"

    def test_cwdがない場合はcontextがNoneになる(self):
        e = from_legacy({"sessionId": "s1"})
        assert e.context is None


# ---------------------------------------------------------------------------
# from_legacy() — データ保全
# ---------------------------------------------------------------------------

class TestFromLegacy_データ保全:
    """from_legacy() は元のペイロードをextensions.legacy_payloadに保存する。"""

    def test_元のペイロードがextensionsに保存される(self):
        payload = {"sessionId": "s1", "transcriptPath": "/t.jsonl"}
        e = from_legacy(payload)
        assert e.extensions["legacy_payload"] == payload

    def test_tool_nameはdataに移される(self):
        e = from_legacy({
            "hook_event_name": "postToolUse",
            "session_id": "s1",
            "tool_name": "Bash",
        })
        assert e.data["tool_name"] == "Bash"

    def test_transcript_pathはdataに移される(self):
        e = from_legacy({"sessionId": "s1", "transcriptPath": "/home/.claude/sess.jsonl"})
        assert e.data["transcript_path"] == "/home/.claude/sess.jsonl"
