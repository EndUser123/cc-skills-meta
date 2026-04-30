"""Tests for shared transcript reader handling all Claude Code JSONL formats."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from skills.gto.__lib.transcript import TranscriptTurn, read_turns, _extract_role_content


def _write_jsonl(path: Path, entries: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


class TestSimpleFormat:
    def test_reads_simple_format(self, tmp_path: Path) -> None:
        p = tmp_path / "t.jsonl"
        _write_jsonl(p, [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ])
        turns = read_turns(p)
        assert len(turns) == 2
        assert turns[0] == TranscriptTurn(role="user", content="hello", turn_number=1)
        assert turns[1] == TranscriptTurn(role="assistant", content="hi there", turn_number=2)

    def test_skips_non_message_entries(self, tmp_path: Path) -> None:
        p = tmp_path / "t.jsonl"
        _write_jsonl(p, [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "hello"},
            {"type": "tool_use", "data": "stuff"},
            {"unknown": "field"},
        ])
        turns = read_turns(p)
        assert len(turns) == 1
        assert turns[0].content == "hello"


class TestNewFormat:
    def test_reads_new_format_string(self, tmp_path: Path) -> None:
        p = tmp_path / "t.jsonl"
        _write_jsonl(p, [
            {"type": "user", "message": {"content": "build the thing"}},
            {"type": "assistant", "message": {"content": "done"}},
        ])
        turns = read_turns(p)
        assert len(turns) == 2
        assert turns[0].role == "user"
        assert turns[0].content == "build the thing"

    def test_reads_new_format_blocks(self, tmp_path: Path) -> None:
        p = tmp_path / "t.jsonl"
        _write_jsonl(p, [
            {"type": "user", "message": {"content": [
                {"type": "text", "text": "part one"},
                {"type": "text", "text": "part two"},
            ]}},
        ])
        turns = read_turns(p)
        assert len(turns) == 1
        assert turns[0].content == "part one part two"

    def test_skips_non_text_blocks(self, tmp_path: Path) -> None:
        p = tmp_path / "t.jsonl"
        _write_jsonl(p, [
            {"type": "user", "message": {"content": [
                {"type": "image", "source": "..."},
                {"type": "text", "text": "visible text"},
            ]}},
        ])
        turns = read_turns(p)
        assert len(turns) == 1
        assert turns[0].content == "visible text"


class TestOldFormat:
    def test_reads_old_format_text(self, tmp_path: Path) -> None:
        p = tmp_path / "t.jsonl"
        _write_jsonl(p, [
            {"sender": "user", "text": "old style message"},
            {"sender": "assistant", "text": "reply"},
        ])
        turns = read_turns(p)
        assert len(turns) == 2
        assert turns[0].content == "old style message"

    def test_reads_old_format_content(self, tmp_path: Path) -> None:
        p = tmp_path / "t.jsonl"
        _write_jsonl(p, [
            {"sender": "user", "content": "alt content field"},
        ])
        turns = read_turns(p)
        assert len(turns) == 1
        assert turns[0].content == "alt content field"


class TestEdgeCases:
    def test_handles_empty_file(self, tmp_path: Path) -> None:
        p = tmp_path / "t.jsonl"
        p.write_text("")
        turns = read_turns(p)
        assert turns == []

    def test_handles_nonexistent_file(self, tmp_path: Path) -> None:
        turns = read_turns(tmp_path / "nope.jsonl")
        assert turns == []

    def test_handles_invalid_json_lines(self, tmp_path: Path) -> None:
        p = tmp_path / "t.jsonl"
        with open(p, "w") as f:
            f.write("not json\n")
            f.write('{"role": "user", "content": "valid"}\n')
            f.write("also not json\n")
        turns = read_turns(p)
        assert len(turns) == 1
        assert turns[0].content == "valid"

    def test_skips_empty_content(self, tmp_path: Path) -> None:
        p = tmp_path / "t.jsonl"
        _write_jsonl(p, [
            {"role": "user", "content": ""},
            {"role": "assistant", "content": "non-empty"},
        ])
        turns = read_turns(p)
        assert len(turns) == 1

    def test_turn_numbers_sequential(self, tmp_path: Path) -> None:
        p = tmp_path / "t.jsonl"
        _write_jsonl(p, [
            {"role": "user", "content": "a"},
            {"role": "assistant", "content": "b"},
            {"role": "user", "content": "c"},
        ])
        turns = read_turns(p)
        assert [t.turn_number for t in turns] == [1, 2, 3]


class TestStalenessFilter:
    def test_staleness_filter_skips_old_files(self, tmp_path: Path) -> None:
        p = tmp_path / "t.jsonl"
        _write_jsonl(p, [{"role": "user", "content": "old"}])
        old_time = time.time() - 10 * 86400
        os.utime(p, (old_time, old_time))
        turns = read_turns(p, max_age_days=7)
        assert turns == []

    def test_staleness_filter_keeps_recent_files(self, tmp_path: Path) -> None:
        p = tmp_path / "t.jsonl"
        _write_jsonl(p, [{"role": "user", "content": "recent"}])
        turns = read_turns(p, max_age_days=7)
        assert len(turns) == 1


class TestExtractRoleContent:
    def test_new_format_non_dict_message(self) -> None:
        role, content = _extract_role_content({"type": "user", "message": "string"})
        assert role is None
        assert content == ""

    def test_old_format_list_content(self) -> None:
        role, content = _extract_role_content({
            "sender": "user",
            "content": [{"type": "text", "text": "list content"}],
        })
        assert role == "user"
        assert content == "list content"
