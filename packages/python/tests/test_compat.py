"""Tests for legacy payload conversion."""

from openhook import EventType, from_legacy, is_openhook


class TestIsOpenhook:
    def test_openhook_payload(self):
        assert is_openhook({"openhook": "0.1", "type": "session.end"}) is True

    def test_legacy_payload(self):
        assert is_openhook({"sessionId": "abc", "transcriptPath": "/t.jsonl"}) is False


class TestFromLegacy:
    def test_claude_payload(self):
        payload = {
            "sessionId": "sess_abc",
            "transcriptPath": "/home/.claude/sess.jsonl",
        }
        e = from_legacy(payload)
        assert e.session_id == "sess_abc"
        assert e.type == EventType.SESSION_END
        assert str(e.transcript_path) == "/home/.claude/sess.jsonl"
        assert e.extensions["legacy_payload"] == payload

    def test_cursor_payload(self):
        e = from_legacy({"conversation_id": "conv_123"})
        assert e.source == "cursor"
        assert e.session_id == "conv_123"

    def test_copilot_tool_end(self):
        e = from_legacy({
            "hook_event_name": "postToolUse",
            "session_id": "gh_sess",
            "tool_name": "Bash",
        })
        assert e.type == EventType.TOOL_END
        assert e.data["tool_name"] == "Bash"

    def test_codex_payload(self):
        e = from_legacy({"thread-id": "t-001"})
        assert e.source == "codex"
        assert e.session_id == "t-001"

    def test_cline_payload(self):
        e = from_legacy({"taskId": "task_xyz"})
        assert e.source == "cline"
        assert e.session_id == "task_xyz"

    def test_kiro_prompt_submit(self):
        e = from_legacy({
            "hook_event_name": "userPromptSubmit",
            "session_id": "kiro_s1",
        })
        assert e.type == EventType.PROMPT_SUBMIT
