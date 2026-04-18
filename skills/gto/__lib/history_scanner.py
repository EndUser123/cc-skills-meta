"""History Scanner - Session transcript chain traversal.

Traverses session transcript chains by following transcript_path links,
detecting cycles, enforcing max depth, and handling corruption.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class HistoryScanner:
    """Scan and traverse session transcript chains."""

    MAX_CHAIN_DEPTH: int = 10

    def __init__(self, sessions_dir: Path) -> None:
        """Initialize scanner with sessions directory.

        Args:
            sessions_dir: Root directory containing session transcript files.
        """
        self.sessions_dir = Path(sessions_dir)

    def find_session_chain(
        self, transcript_path: Path
    ) -> tuple[list[Path], list[str]]:
        """Traverse transcript chain following transcript_path links.

        Args:
            transcript_path: Path to starting transcript file.

        Returns:
            Tuple of (chain: list of Path objects in chronological order (oldest first),
                     missing: list of transcript_path values that could not be resolved)
        """
        # Build chain in traversal order (newest to oldest), then reverse
        reverse_chain: list[Path] = []
        missing: list[str] = []
        seen: set[str] = set()
        current = Path(transcript_path).resolve()
        current_relative = self._relative_to_sessions(current)

        while current_relative and len(reverse_chain) < self.MAX_CHAIN_DEPTH:
            # Check for cycle
            if str(current_relative) in seen:
                break
            seen.add(str(current_relative))

            # Add to reverse chain (we traverse newest -> oldest)
            if current.exists() and current.is_file():
                reverse_chain.append(current)
            else:
                missing.append(str(current_relative))
                break

            # Read transcript_path link from the LAST entry in the file
            prior_ref = self._read_transcript_prior(current)
            if prior_ref is None:
                break

            # Validate path - reject path traversal attempts
            if not self._is_safe_path(prior_ref):
                missing.append(prior_ref)
                break

            # Resolve relative to current transcript's directory
            current = (current.parent / prior_ref).resolve()
            current_relative = self._relative_to_sessions(current)

        # Reverse to get oldest -> newest (chronological order)
        chain = list(reversed(reverse_chain))
        return chain, missing

    def _relative_to_sessions(self, path: Path) -> Path | None:
        """Return path relative to sessions_dir, or None if outside sessions_dir."""
        try:
            return path.resolve().relative_to(self.sessions_dir.resolve())
        except ValueError:
            return None

    def _read_transcript_prior(self, transcript_path: Path) -> str | None:
        """Read transcript_path from the last JSON line of a transcript file.

        Returns:
            The transcript_path value from the last entry, or None if not present.
        """
        try:
            with open(transcript_path, encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
        except (OSError, UnicodeDecodeError):
            return None

        if not lines:
            return None

        # Parse last line
        try:
            entry = json.loads(lines[-1])
        except json.JSONDecodeError:
            return None

        return entry.get("transcript_path")

    def _is_safe_path(self, path_ref: str) -> bool:
        """Reject path traversal attempts.

        Args:
            path_ref: The transcript_path value to validate.

        Returns:
            False if path is unsafe (traversal or absolute outside sessions), True otherwise.
        """
        # Reject absolute paths pointing outside sessions_dir
        if Path(path_ref).is_absolute():
            # Allow absolute paths within sessions_dir
            try:
                (self.sessions_dir / path_ref).resolve().relative_to(self.sessions_dir.resolve())
                return True
            except ValueError:
                return False

        # Reject path traversal (..)
        if ".." in path_ref:
            return False

        return True
