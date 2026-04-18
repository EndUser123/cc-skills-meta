"""Tests for HistoryScanner.find_session_chain method."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.history_scanner import HistoryScanner


class TestFindSessionChain:
    """Tests for find_session_chain traversal."""

    def _write_transcript(self, path: Path, prior_path: str | None = None) -> None:
        """Write a minimal transcript JSONL file.

        Args:
            path: Path to write
            prior_path: Optional transcript_path link to prior transcript
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        entry: dict[str, str] = {"role": "user", "content": "test message"}
        if prior_path is not None:
            entry["transcript_path"] = prior_path
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def test_single_transcript_no_prior(self, tmp_path: Path) -> None:
        """Chain with single transcript and no prior link returns just that transcript."""
        scanner = HistoryScanner(tmp_path)

        # Create a single transcript with no transcript_path
        transcript_file = tmp_path / "session.jsonl"
        self._write_transcript(transcript_file)

        chain, missing = scanner.find_session_chain(transcript_file)

        assert chain == [transcript_file]
        assert missing == []

    def test_chain_traversal_two_transcripts(self, tmp_path: Path) -> None:
        """Chain traverses backward through two transcripts."""
        scanner = HistoryScanner(tmp_path)

        # Create prior transcript
        prior = tmp_path / "prior.jsonl"
        self._write_transcript(prior)

        # Create current transcript pointing to prior
        current = tmp_path / "current.jsonl"
        self._write_transcript(current, prior_path="prior.jsonl")

        chain, missing = scanner.find_session_chain(current)

        assert chain == [prior, current]
        assert missing == []

    def test_chain_traversal_three_transcripts(self, tmp_path: Path) -> None:
        """Chain traverses backward through three transcripts."""
        scanner = HistoryScanner(tmp_path)

        # Create oldest
        oldest = tmp_path / "oldest.jsonl"
        self._write_transcript(oldest)

        # Create middle pointing to oldest
        middle = tmp_path / "middle.jsonl"
        self._write_transcript(middle, prior_path="oldest.jsonl")

        # Create current pointing to middle
        current = tmp_path / "current.jsonl"
        self._write_transcript(current, prior_path="middle.jsonl")

        chain, missing = scanner.find_session_chain(current)

        assert chain == [oldest, middle, current]
        assert missing == []

    def test_max_depth_limit(self, tmp_path: Path) -> None:
        """Chain traversal stops at MAX_CHAIN_DEPTH (10)."""
        scanner = HistoryScanner(tmp_path)

        # Create chain longer than MAX_CHAIN_DEPTH
        chain_files: list[Path] = []
        for i in range(15):
            fname = f"session_{i:02d}.jsonl"
            prior = f"session_{i-1:02d}.jsonl" if i > 0 else None
            path = tmp_path / fname
            self._write_transcript(path, prior_path=prior)
            chain_files.append(path)

        # Start from the last (most recent) transcript
        chain, missing = scanner.find_session_chain(chain_files[-1])

        # Should have at most MAX_CHAIN_DEPTH entries
        assert len(chain) <= scanner.MAX_CHAIN_DEPTH
        assert missing == []

    def test_missing_transcript_file(self, tmp_path: Path) -> None:
        """Missing transcript file is recorded in missing list and stops traversal."""
        scanner = HistoryScanner(tmp_path)

        # Create current pointing to missing prior
        current = tmp_path / "current.jsonl"
        self._write_transcript(current, prior_path="missing.jsonl")

        chain, missing = scanner.find_session_chain(current)

        # Should have current in chain but missing prior
        assert chain == [current]
        assert "missing.jsonl" in missing or any("missing" in m for m in missing)

    def test_missing_field_stops_traversal(self, tmp_path: Path) -> None:
        """Missing transcript_path field stops traversal gracefully."""
        scanner = HistoryScanner(tmp_path)

        # Create first with no prior link
        first = tmp_path / "first.jsonl"
        self._write_transcript(first)

        # Create second pointing to first
        second = tmp_path / "second.jsonl"
        self._write_transcript(second, prior_path="first.jsonl")

        chain, missing = scanner.find_session_chain(second)

        assert chain == [first, second]
        assert missing == []

    def test_corrupt_jsonl_handled(self, tmp_path: Path) -> None:
        """Corrupt JSONL lines are skipped, traversal continues."""
        scanner = HistoryScanner(tmp_path)

        # Create a prior transcript
        prior = tmp_path / "prior.jsonl"
        self._write_transcript(prior)

        # Create current transcript with corrupt line before valid entry
        current = tmp_path / "current.jsonl"
        current.parent.mkdir(parents=True, exist_ok=True)
        with open(current, "w", encoding="utf-8") as f:
            f.write("NOT VALID JSON\n")
            f.write(json.dumps({"role": "user", "content": "test", "transcript_path": "prior.jsonl"}) + "\n")

        chain, missing = scanner.find_session_chain(current)

        assert prior in chain
        assert current in chain
        assert missing == []

    def test_cycle_detection(self, tmp_path: Path) -> None:
        """Cycle detection aborts on repeated path."""
        scanner = HistoryScanner(tmp_path)

        # Create A -> B -> A cycle
        a = tmp_path / "a.jsonl"
        b = tmp_path / "b.jsonl"

        # B points to A
        self._write_transcript(b, prior_path="a.jsonl")
        # A points to B (creating cycle)
        self._write_transcript(a, prior_path="b.jsonl")

        chain, _missing = scanner.find_session_chain(a)

        # Should stop when cycle is detected
        assert len(chain) <= 2

    def test_path_traversal_rejected(self, tmp_path: Path) -> None:
        """Path with .. escape sequence is rejected."""
        scanner = HistoryScanner(tmp_path)

        # Create current with path traversal attempt
        current = tmp_path / "current.jsonl"
        self._write_transcript(current, prior_path="../escape.jsonl")

        chain, missing = scanner.find_session_chain(current)

        # Should stop and record the corrupt path
        assert chain == [current]
        assert len(missing) >= 1

    def test_absolute_path_outside_rejected(self, tmp_path: Path) -> None:
        """Absolute path outside sessions dir is rejected."""
        scanner = HistoryScanner(tmp_path)

        # Create current with absolute path pointing outside
        current = tmp_path / "current.jsonl"
        self._write_transcript(current, prior_path="C:/windows/system32/config.jsonl")

        chain, missing = scanner.find_session_chain(current)

        # Should stop and record the invalid path
        assert chain == [current]
        assert len(missing) >= 1

    def test_relative_path_resolved_correctly(self, tmp_path: Path) -> None:
        """Relative transcript_path is resolved relative to current transcript's directory."""
        scanner = HistoryScanner(tmp_path)

        # Create a subdirectory with a prior transcript
        subdir = tmp_path / "subdir"
        subdir.mkdir(parents=True, exist_ok=True)

        prior = subdir / "prior.jsonl"
        self._write_transcript(prior)

        # Create current in subdir pointing to prior (relative)
        current = subdir / "current.jsonl"
        self._write_transcript(current, prior_path="prior.jsonl")

        chain, missing = scanner.find_session_chain(current)

        assert prior in chain
        assert current in chain
        assert missing == []

    def test_empty_missing_list_on_success(self, tmp_path: Path) -> None:
        """Missing list is empty when all transcripts found."""
        scanner = HistoryScanner(tmp_path)

        # Create chain of 3 valid transcripts
        oldest = tmp_path / "oldest.jsonl"
        middle = tmp_path / "middle.jsonl"
        current = tmp_path / "current.jsonl"

        self._write_transcript(oldest)
        self._write_transcript(middle, prior_path="oldest.jsonl")
        self._write_transcript(current, prior_path="middle.jsonl")

        chain, missing = scanner.find_session_chain(current)

        assert len(chain) == 3
        assert missing == []
