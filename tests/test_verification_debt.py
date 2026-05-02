"""Tests for verification_debt detector — detects edits without test verification."""
import json
from pathlib import Path

from skills.gto.__lib.verification_debt import detect_verification_debt


def _make_edit_entry(file_path: str, entry_id: str = "call_1") -> dict:
    return {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": entry_id,
                    "name": "Edit",
                    "input": {"file_path": file_path, "old_string": "old", "new_string": "new"},
                }
            ],
        },
    }


def _make_bash_entry(command: str, entry_id: str = "call_bash") -> dict:
    return {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": entry_id,
                    "name": "Bash",
                    "input": {"command": command},
                }
            ],
        },
    }


class TestVerificationDebtDetector:
    def test_edit_without_test_detected(self, tmp_path):
        tf = tmp_path / "test.jsonl"
        tf.write_text(json.dumps(_make_edit_entry("src/module.py")) + "\n")
        findings = detect_verification_debt(tf)
        assert len(findings) == 1
        assert findings[0].id == "VERIFY-001"
        assert "module.py" in findings[0].description

    def test_edit_with_test_not_flagged(self, tmp_path):
        tf = tmp_path / "test.jsonl"
        lines = [
            json.dumps(_make_edit_entry("src/module.py", "e1")),
            json.dumps(_make_bash_entry("pytest tests/test_module.py", "b1")),
        ]
        tf.write_text("\n".join(lines) + "\n")
        findings = detect_verification_debt(tf)
        assert findings == []

    def test_edit_to_md_file_ignored(self, tmp_path):
        tf = tmp_path / "test.jsonl"
        tf.write_text(json.dumps(_make_edit_entry("README.md")) + "\n")
        findings = detect_verification_debt(tf)
        assert findings == []

    def test_empty_transcript_returns_empty(self, tmp_path):
        tf = tmp_path / "test.jsonl"
        tf.write_text("")
        findings = detect_verification_debt(tf)
        assert findings == []

    def test_nonexistent_returns_empty(self, tmp_path):
        findings = detect_verification_debt(tmp_path / "nope.jsonl")
        assert findings == []

    def test_multiple_edits_deduped_by_file(self, tmp_path):
        tf = tmp_path / "test.jsonl"
        lines = [
            json.dumps(_make_edit_entry("src/a.py", "e1")),
            json.dumps(_make_edit_entry("src/a.py", "e2")),
        ]
        tf.write_text("\n".join(lines) + "\n")
        findings = detect_verification_debt(tf)
        assert len(findings) == 1
