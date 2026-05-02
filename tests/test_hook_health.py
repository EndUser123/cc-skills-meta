"""Tests for hook_health detector — scans transcript for hook errors."""
import json
from pathlib import Path

from skills.gto.__lib.hook_health import detect_hook_errors


def _make_hook_attachment(
    hook_name: str = "SessionStart:startup",
    exit_code: int = 0,
    stderr: str = "",
    att_type: str = "hook_success",
) -> dict:
    return {
        "type": "user",
        "message": {"content": "..."},
        "attachment": {
            "type": att_type,
            "hookName": hook_name,
            "exitCode": exit_code,
            "stderr": stderr,
            "stdout": "",
            "durationMs": 100,
        },
    }


class TestHookHealthDetector:
    def test_no_errors_returns_empty(self, tmp_path):
        tf = tmp_path / "test.jsonl"
        tf.write_text(json.dumps(_make_hook_attachment()) + "\n")
        findings = detect_hook_errors(tf)
        assert findings == []

    def test_session_start_error_detected(self, tmp_path):
        tf = tmp_path / "test.jsonl"
        tf.write_text(
            json.dumps(
                _make_hook_attachment(
                    hook_name="SessionStart:startup",
                    exit_code=1,
                    stderr="ImportError: no module named foo",
                    att_type="hook_non_blocking_error",
                )
            )
            + "\n"
        )
        findings = detect_hook_errors(tf)
        assert len(findings) == 1
        assert findings[0].id.startswith("HOOK-")
        assert findings[0].severity == "high"
        assert "SessionStart" in findings[0].title

    def test_pretooluse_block_exit2_ignored(self, tmp_path):
        """Exit code 2 from PreToolUse is intentional blocking, not an error."""
        tf = tmp_path / "test.jsonl"
        tf.write_text(
            json.dumps(
                _make_hook_attachment(
                    hook_name="PreToolUse:edit",
                    exit_code=2,
                    stderr="Blocked: dangerous pattern",
                    att_type="hook_non_blocking_error",
                )
            )
            + "\n"
        )
        findings = detect_hook_errors(tf)
        assert findings == []

    def test_nonexistent_transcript_returns_empty(self, tmp_path):
        findings = detect_hook_errors(tmp_path / "nonexistent.jsonl")
        assert findings == []

    def test_empty_transcript_returns_empty(self, tmp_path):
        tf = tmp_path / "test.jsonl"
        tf.write_text("")
        findings = detect_hook_errors(tf)
        assert findings == []

    def test_multiple_errors_deduped_by_hook(self, tmp_path):
        tf = tmp_path / "test.jsonl"
        lines = [
            json.dumps(
                _make_hook_attachment(
                    hook_name="SessionStart:startup",
                    exit_code=1,
                    stderr="error 1",
                    att_type="hook_non_blocking_error",
                )
            ),
            json.dumps(
                _make_hook_attachment(
                    hook_name="SessionStart:startup",
                    exit_code=1,
                    stderr="error 2",
                    att_type="hook_non_blocking_error",
                )
            ),
        ]
        tf.write_text("\n".join(lines) + "\n")
        findings = detect_hook_errors(tf)
        assert len(findings) == 1
