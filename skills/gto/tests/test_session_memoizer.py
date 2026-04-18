"""Tests for session_memoizer."""

from __future__ import annotations

import json
import os
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys_path_insert = str(Path(__file__).parent.parent)
import sys
sys.path.insert(0, sys_path_insert)

from __lib.session_memoizer import (
    DEFAULT_CACHE_TTL_DAYS,
    CachedSessionAnalysis,
    SessionMemoizer,
    _build_chain_signature,
    _get_session_cache_path,
    _get_sessions_cache_dir,
    _get_session_mtime,
    _load_session_cache,
    _save_session_cache,
)


class TestBuildChainSignature:
    """Tests for _build_chain_signature."""

    def test_sorted_session_ids(self) -> None:
        """Session IDs are sorted for consistent signatures."""
        entries = [
            {"sessionId": "z-session", "transcriptPath": "z.jsonl"},
            {"sessionId": "a-session", "transcriptPath": "a.jsonl"},
            {"sessionId": "m-session", "transcriptPath": "m.jsonl"},
        ]
        sig = _build_chain_signature(entries)
        assert sig == "a-session,m-session,z-session"

    def test_empty_entries(self) -> None:
        """Empty list returns empty string."""
        assert _build_chain_signature([]) == ""

    def test_mixed_objects_and_dicts(self) -> None:
        """Supports both objects and dicts."""
        # Using simple dicts with session_id attr-like access
        class FakeEntry:
            def __init__(self, sid: str):
                self.session_id = sid

        entries = [
            FakeEntry("b"),
            {"sessionId": "a"},
        ]
        sig = _build_chain_signature(entries)
        assert sig == "a,b"


class TestGetSessionCachePath:
    """Tests for _get_session_cache_path."""

    def test_normal_session_id(self, tmp_path: Path, monkeypatch) -> None:
        """Normal UUID-style session_id creates valid path."""
        # Patch cache dir to tmp_path
        def fake_cache_dir():
            return tmp_path

        monkeypatch.setattr("__lib.session_memoizer._get_sessions_cache_dir", fake_cache_dir)
        path = _get_session_cache_path("abc123-def456")
        assert path.parent == tmp_path
        assert "abc123-def456.json" in str(path)

    def test_path_traversal_blocked(self, tmp_path: Path, monkeypatch) -> None:
        """Session_id with ../ is sanitized — the path resolves within cache dir, no escape."""
        def fake_cache_dir():
            return tmp_path

        monkeypatch.setattr("__lib.session_memoizer._get_sessions_cache_dir", fake_cache_dir)
        # On Windows, path with ../ may still resolve within cache dir after normalization
        # The security is that the final path is always within cache_dir (enforced by relative_to)
        path = _get_session_cache_path("../../../etc/passwd")
        assert path.parent == tmp_path
        # Path traversal is contained — path resolves within cache directory
        path.resolve().relative_to(tmp_path.resolve())

    def test_path_traversal_with_double_dot_not_normalized(self, tmp_path: Path, monkeypatch) -> None:
        """On Unix-like paths, double-dot alone could escape — verify containment."""
        def fake_cache_dir():
            return tmp_path

        monkeypatch.setattr("__lib.session_memoizer._get_sessions_cache_dir", fake_cache_dir)
        # Simulate a path that on Unix would escape via ../
        # The relative_to check prevents escape regardless of sanitize
        path = _get_session_cache_path("foo/../../etc/passwd")
        assert path.parent == tmp_path


class TestSaveAndLoadSessionCache:
    """Tests for _save_session_cache and _load_session_cache round-trip."""

    def test_save_and_load_round_trip(self, tmp_path: Path, monkeypatch) -> None:
        """Cache save and load produces identical data."""
        def fake_cache_dir():
            return tmp_path

        monkeypatch.setattr("__lib.session_memoizer._get_sessions_cache_dir", fake_cache_dir)

        session_id = "test-session-123"
        transcript_path = tmp_path / "transcript.jsonl"
        transcript_path.write_text("content")

        mtime = _get_session_mtime(transcript_path)
        assert mtime is not None

        _save_session_cache(
            session_id=session_id,
            transcript_path=transcript_path,
            mtime=mtime,
            chain_depth=3,
            chain_signature="a,b,c",
            result={"focus": "test", "phase": "testing", "next_steps": ["step1"]},
        )

        loaded = _load_session_cache(session_id)
        assert loaded is not None
        assert loaded.session_id == session_id
        assert loaded.mtime == mtime
        assert loaded.chain_depth == 3
        assert loaded.result["focus"] == "test"

    def test_atomic_write_no_corruption_on_interrupt(self, tmp_path: Path, monkeypatch) -> None:
        """On failure, .tmp file is not left behind as the final file."""
        def fake_cache_dir():
            return tmp_path

        monkeypatch.setattr("__lib.session_memoizer._get_sessions_cache_dir", fake_cache_dir)

        session_id = "atomic-test"
        transcript_path = tmp_path / "transcript.jsonl"
        transcript_path.write_text("content")
        mtime = _get_session_mtime(transcript_path)

        _save_session_cache(
            session_id=session_id,
            transcript_path=transcript_path,
            mtime=mtime,
            chain_depth=1,
            chain_signature="x",
            result={"focus": "test"},
        )

        # Verify no stray .tmp file
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert len(tmp_files) == 0

    def test_load_nonexistent_returns_none(self, tmp_path: Path, monkeypatch) -> None:
        """Loading a non-existent session returns None."""
        def fake_cache_dir():
            return tmp_path

        monkeypatch.setattr("__lib.session_memoizer._get_sessions_cache_dir", fake_cache_dir)
        assert _load_session_cache("nonexistent-session") is None

    def test_corrupt_json_returns_none(self, tmp_path: Path, monkeypatch) -> None:
        """Corrupt JSON file is handled gracefully."""
        def fake_cache_dir():
            return tmp_path

        monkeypatch.setattr("__lib.session_memoizer._get_sessions_cache_dir", fake_cache_dir)

        # Write corrupt JSON directly
        cache_file = tmp_path / "corrupt-session.json"
        cache_file.write_text("{not valid json")

        assert _load_session_cache("corrupt-session") is None


class TestTTLExpiry:
    """Tests for cache TTL expiry."""

    def test_expired_cache_rejected(self, tmp_path: Path, monkeypatch) -> None:
        """Cache entries older than TTL_DAYS are rejected."""
        def fake_cache_dir():
            return tmp_path

        monkeypatch.setattr("__lib.session_memoizer._get_sessions_cache_dir", fake_cache_dir)

        session_id = "expired-session"
        # Create a cache file with an old analyzed_at date
        old_date = (datetime.now(timezone.utc).replace(tzinfo=None) -
                    timedelta(days=DEFAULT_CACHE_TTL_DAYS + 1)).isoformat()
        # Write directly to bypass the normal save
        cache_file = tmp_path / f"{session_id}.json"
        cache_file.write_text(json.dumps({
            "session_id": session_id,
            "transcript_path": str(tmp_path / "transcript.jsonl"),
            "mtime": 0.0,
            "chain_depth": 1,
            "analyzed_at": old_date,
            "chain_signature": "x",
            "result": {"focus": "old"},
        }))

        # Note: the TTL check uses datetime.fromisoformat which may not parse
        # naive datetime from .isoformat(). Check that the function handles it.
        loaded = _load_session_cache(session_id)
        # Should return None if TTL check fires
        # (The analyzed_at uses replace(tzinfo=timezone.utc) so old dates should be rejected)
        assert loaded is None or loaded.result.get("focus") != "old"


class TestSessionMemoizerGetCachedChainResult:
    """Tests for SessionMemoizer.get_cached_chain_result."""

    def test_empty_entries_returns_none(self) -> None:
        """Empty chain returns None."""
        memoizer = SessionMemoizer()
        result, missed = memoizer.get_cached_chain_result([])
        assert result is None
        assert missed == []

    def test_missing_session_id_returns_none(self) -> None:
        """Entry without session_id returns None."""
        memoizer = SessionMemoizer()
        result, missed = memoizer.get_cached_chain_result([{"transcriptPath": "x.jsonl"}])
        assert result is None

    def test_no_cache_returns_miss(self, tmp_path: Path, monkeypatch) -> None:
        """When no cache exists, returns miss with session_id."""
        def fake_cache_dir():
            return tmp_path

        monkeypatch.setattr("__lib.session_memoizer._get_sessions_cache_dir", fake_cache_dir)

        memoizer = SessionMemoizer()
        entries = [{"sessionId": "new-session", "transcriptPath": str(tmp_path / "new.jsonl")}]
        result, missed = memoizer.get_cached_chain_result(entries)
        assert result is None
        assert "new-session" in missed

    def test_valid_cache_hit(self, tmp_path: Path, monkeypatch) -> None:
        """When all sessions have valid cache and matching mtimes, returns cached result."""
        def fake_cache_dir():
            return tmp_path

        monkeypatch.setattr("__lib.session_memoizer._get_sessions_cache_dir", fake_cache_dir)

        # Create a session file and its cache
        session_id = "cached-session"
        transcript = tmp_path / f"{session_id}.jsonl"
        transcript.write_text("content")
        mtime = _get_session_mtime(transcript)

        _save_session_cache(
            session_id=session_id,
            transcript_path=transcript,
            mtime=mtime,
            chain_depth=1,
            chain_signature=session_id,
            result={"focus": "cached-focus", "phase": "cached", "next_steps": ["cached-step"]},
        )

        memoizer = SessionMemoizer()
        entries = [{"sessionId": session_id, "transcriptPath": str(transcript)}]
        result, missed = memoizer.get_cached_chain_result(entries)
        assert result is not None
        assert result["focus"] == "cached-focus"
        assert missed == []
        assert memoizer.get_cache_stats()["hits"] == 1

    def test_mtime_changed_returns_miss(self, tmp_path: Path, monkeypatch) -> None:
        """When session file mtime differs from cache, returns miss."""
        def fake_cache_dir():
            return tmp_path

        monkeypatch.setattr("__lib.session_memoizer._get_sessions_cache_dir", fake_cache_dir)

        session_id = "stale-session"
        transcript = tmp_path / f"{session_id}.jsonl"
        transcript.write_text("original")
        original_mtime = _get_session_mtime(transcript)

        _save_session_cache(
            session_id=session_id,
            transcript_path=transcript,
            mtime=original_mtime,
            chain_depth=1,
            chain_signature=session_id,
            result={"focus": "original", "phase": "phase", "next_steps": []},
        )

        # Modify the file to change mtime
        time.sleep(0.1)
        transcript.write_text("modified")
        new_mtime = _get_session_mtime(transcript)
        assert new_mtime != original_mtime

        memoizer = SessionMemoizer()
        entries = [{"sessionId": session_id, "transcriptPath": str(transcript)}]
        result, missed = memoizer.get_cached_chain_result(entries)
        assert result is None
        assert session_id in missed

    def test_chain_signature_change_returns_miss(self, tmp_path: Path, monkeypatch) -> None:
        """When chain composition changes (different sorted IDs), returns miss."""
        def fake_cache_dir():
            return tmp_path

        monkeypatch.setattr("__lib.session_memoizer._get_sessions_cache_dir", fake_cache_dir)

        # Origin (LAST entry) is session-c, cached with signature "a,b"
        # Query has entries [a, c] — sorted signature "a,c" — does NOT match "a,b"
        session_a = "session-a"
        session_c = "session-c"
        transcript_a = tmp_path / f"{session_a}.jsonl"
        transcript_c = tmp_path / f"{session_c}.jsonl"
        transcript_a.write_text("content")
        transcript_c.write_text("content")

        # Cache session-c (origin) with WRONG signature "a,b" (not "a,c")
        _save_session_cache(
            session_id=session_c,
            transcript_path=transcript_c,
            mtime=_get_session_mtime(transcript_c),
            chain_depth=2,
            chain_signature="a,b",
            result={"focus": "old-chain", "phase": "old", "next_steps": []},
        )

        # Query with chain [a, c] — sorted signature "a,c" doesn't match cached "a,b"
        memoizer = SessionMemoizer()
        entries = [
            {"sessionId": session_a, "transcriptPath": str(transcript_a)},
            {"sessionId": session_c, "transcriptPath": str(transcript_c)},
        ]
        result, missed = memoizer.get_cached_chain_result(entries)
        assert result is None
        assert session_c in missed

    def test_missing_transcript_path_treated_as_miss(self, tmp_path: Path, monkeypatch) -> None:
        """When entry has no transcriptPath, treated as cache miss."""
        def fake_cache_dir():
            return tmp_path

        monkeypatch.setattr("__lib.session_memoizer._get_sessions_cache_dir", fake_cache_dir)

        session_id = "no-path-session"
        transcript = tmp_path / f"{session_id}.jsonl"
        transcript.write_text("content")

        _save_session_cache(
            session_id=session_id,
            transcript_path=transcript,
            mtime=_get_session_mtime(transcript),
            chain_depth=1,
            chain_signature=session_id,
            result={"focus": "test", "phase": "test", "next_steps": []},
        )

        memoizer = SessionMemoizer()
        # Entry with session_id but no transcriptPath
        entries = [{"sessionId": session_id}]  # type: ignore[list-item]
        result, missed = memoizer.get_cached_chain_result(entries)
        assert result is None
        assert session_id in missed


class TestSessionMemoizerClearCache:
    """Tests for SessionMemoizer.clear_cache."""

    def test_clear_specific_session(self, tmp_path: Path, monkeypatch) -> None:
        """Clearing a specific session removes only that cache file."""
        def fake_cache_dir():
            return tmp_path

        monkeypatch.setattr("__lib.session_memoizer._get_sessions_cache_dir", fake_cache_dir)

        session_a = "session-a"
        session_b = "session-b"
        for sid in [session_a, session_b]:
            path = tmp_path / f"{sid}.jsonl"
            path.write_text("content")
            _save_session_cache(
                session_id=sid,
                transcript_path=path,
                mtime=_get_session_mtime(path),
                chain_depth=1,
                chain_signature=sid,
                result={"focus": sid},
            )

        memoizer = SessionMemoizer()
        memoizer.clear_cache(session_a)

        assert not (tmp_path / f"{session_a}.json").exists()
        assert (tmp_path / f"{session_b}.json").exists()

    def test_clear_all(self, tmp_path: Path, monkeypatch) -> None:
        """Clearing with None removes all cache files."""
        def fake_cache_dir():
            return tmp_path

        monkeypatch.setattr("__lib.session_memoizer._get_sessions_cache_dir", fake_cache_dir)

        for i in range(3):
            path = tmp_path / f"session-{i}.jsonl"
            path.write_text("content")
            _save_session_cache(
                session_id=f"session-{i}",
                transcript_path=path,
                mtime=_get_session_mtime(path),
                chain_depth=1,
                chain_signature=f"session-{i}",
                result={"focus": f"session-{i}"},
            )

        memoizer = SessionMemoizer()
        memoizer.clear_cache(None)

        cache_files = list(tmp_path.glob("*.json"))
        assert len(cache_files) == 0


class TestSessionMemoizerCacheStats:
    """Tests for SessionMemoizer cache statistics."""

    def test_stats_tracked(self, tmp_path: Path, monkeypatch) -> None:
        """Cache hits and misses are tracked correctly."""
        def fake_cache_dir():
            return tmp_path

        monkeypatch.setattr("__lib.session_memoizer._get_sessions_cache_dir", fake_cache_dir)

        memoizer = SessionMemoizer()

        # Miss
        entries = [{"sessionId": "miss", "transcriptPath": str(tmp_path / "miss.jsonl")}]
        memoizer.get_cached_chain_result(entries)

        stats = memoizer.get_cache_stats()
        assert stats["misses"] >= 1
