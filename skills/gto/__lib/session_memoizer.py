"""Session Memoizer - Per-session caching for GTO session chain analysis.

Priority: P1 (performance optimization)
Purpose: Avoid re-analyzing unchanged sessions in the chain.

Mechanism:
  - Each session's ChainAnalysisResult cached to ~/.claude/.evidence/gto-sessions/{session_id}.json
  - Cache validity: session file mtime matches cached mtime at write time
  - On cache hit: load cached result without calling LLM
  - On cache miss: run analysis, write cache
  - Chain-level: if chain composition (sorted session IDs) unchanged AND all sessions
    have valid cache hits, return cached chain result directly

Cache structure (~/.claude/.evidence/gto-sessions/{session_id}.json):
  {
    "session_id": "abc123",
    "transcript_path": "/path/to/abc123.jsonl",
    "mtime": 1712234567.123,
    "chain_depth": 5,
    "analyzed_at": "2026-04-05T...",
    "chain_signature": "a,b,c,d,e",  # sorted session IDs at time of analysis
    "result": {
      "focus": "...",
      "phase": "...",
      "next_steps": [...],
      "confidence": 0.85,
      "error": null,
      "transcripts_processed": 5
    }
  }
"""

from __future__ import annotations

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default cache TTL: 7 days
DEFAULT_CACHE_TTL_DAYS = 7

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def _get_sessions_cache_dir() -> Path:
    """Get the session memoization cache directory."""
    try:
        cache_dir = Path.home() / ".claude" / ".evidence" / "gto-sessions"
    except RuntimeError:
        # HOME not set — fall back to temp directory
        temp_base = os.environ.get("TEMP", "/tmp")
        cache_dir = Path(temp_base) / ".claude" / ".evidence" / "gto-sessions"
        logger.warning("HOME not set, using fallback cache dir: %s", cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _get_session_cache_path(session_id: str) -> Path:
    """Get cache file path for a session. Path is validated to be within cache directory."""
    cache_dir = _get_sessions_cache_dir()
    # Defensive: session_id should be a UUID from Claude Code internals, but
    # validate containment to prevent path traversal
    safe_name = session_id.replace("/", "_").replace("\\", "_").replace("..", "_")
    path = cache_dir / f"{safe_name}.json"
    # Security: enforce path stays within cache directory
    try:
        path.resolve().relative_to(cache_dir.resolve())
    except ValueError:
        logger.warning("Path traversal attempt blocked: session_id=%s", session_id)
        return cache_dir / f"_blocked_{safe_name[:8]}.json"
    return path


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class CachedSessionAnalysis:
    """Cached analysis result for a single session."""
    session_id: str
    transcript_path: Path
    mtime: float  # session file mtime at time of caching
    chain_depth: int
    analyzed_at: str
    chain_signature: str  # sorted session IDs when this was analyzed
    result: dict[str, Any]


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


def _load_session_cache(session_id: str) -> CachedSessionAnalysis | None:
    """Load cached analysis for a session, or None if cache miss/invalid."""
    cache_path = _get_session_cache_path(session_id)

    try:
        with open(cache_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Failed to load session cache for %s: %s", session_id, e)
        return None

    # TTL check: reject entries older than DEFAULT_CACHE_TTL_DAYS
    analyzed_at_str = data.get("analyzed_at", "")
    if analyzed_at_str:
        try:
            analyzed_at = datetime.fromisoformat(analyzed_at_str).replace(tzinfo=timezone.utc)
            expiry = datetime.now(timezone.utc) - timedelta(days=DEFAULT_CACHE_TTL_DAYS)
            if analyzed_at < expiry:
                logger.info("Session cache for %s expired (TTL=%d days)", session_id, DEFAULT_CACHE_TTL_DAYS)
                return None
        except (ValueError, TypeError):
            pass

    return CachedSessionAnalysis(
        session_id=data.get("session_id", ""),
        transcript_path=Path(data.get("transcript_path", "")),
        mtime=data.get("mtime", 0.0),
        chain_depth=data.get("chain_depth", 0),
        analyzed_at=analyzed_at_str,
        chain_signature=data.get("chain_signature", ""),
        result=data.get("result", {}),
    )


def _save_session_cache(
    session_id: str,
    transcript_path: Path,
    mtime: float,
    chain_depth: int,
    chain_signature: str,
    result: dict[str, Any],
) -> None:
    """Save analysis result to session cache atomically.

    Uses write-to-temp-then-replace pattern to prevent corruption on crash.
    Re-reads mtime inside to avoid TOCTOU between capture and write.
    """
    cache_path = _get_session_cache_path(session_id)
    try:
        # Re-read mtime to avoid TOCTOU: file could change between capture and write
        current_mtime = _get_session_mtime(transcript_path)
        if current_mtime is not None and current_mtime != mtime:
            logger.warning(
                "Session %s: mtime changed between capture and write "
                "(captured=%.3f, current=%.3f) — skipping cache write",
                session_id, mtime, current_mtime,
            )
            return

        data = {
            "session_id": session_id,
            "transcript_path": str(transcript_path),
            "mtime": current_mtime if current_mtime is not None else mtime,
            "chain_depth": chain_depth,
            "analyzed_at": datetime.now().isoformat(),
            "chain_signature": chain_signature,
            "result": result,
        }
        # Atomic write: write to .tmp, then os.replace() to commit
        tmp_path = cache_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, cache_path)
    except OSError as e:
        logger.warning("Failed to save session cache for %s: %s", session_id, e)


def _get_session_mtime(transcript_path: Path) -> float | None:
    """Get session file mtime, or None if file doesn't exist."""
    try:
        if transcript_path.exists():
            return transcript_path.stat().st_mtime
    except FileNotFoundError:
        pass
    except OSError as e:
        logger.warning("Failed to get mtime for %s: %s", transcript_path, e)
    return None


def _build_chain_signature(entries: list) -> str:
    """Build a signature string from session IDs in the chain (sorted for consistency)."""
    # Support both SessionChainEntry objects and dicts
    session_ids = []
    for entry in entries:
        sid = getattr(entry, "session_id", None) or entry.get("sessionId", "")
        if sid:
            session_ids.append(sid)
    return ",".join(sorted(session_ids))


# ---------------------------------------------------------------------------
# SessionMemoizer class
# ---------------------------------------------------------------------------


class SessionMemoizer:
    """Handles per-session memoization for chain analysis results.

    Checks cache validity via session file mtime. If the chain composition
    hasn't changed and all sessions have valid cache hits, returns cached
    ChainAnalysisResult without calling the LLM.
    """

    def __init__(self):
        self._cache_hits = 0
        self._cache_misses = 0

    def get_cached_chain_result(
        self,
        entries: list,
    ) -> tuple[dict[str, Any] | None, list[str]]:
        """Check if the full chain result can be served from cache.

        Args:
            entries: List of SessionChainEntry objects (or dicts)

        Returns:
            Tuple of (cached_result_or_None, list_of_missed_session_ids)
            If the chain composition unchanged and ALL sessions cached with valid mtimes,
            returns the cached result (from the current/origin session's cache).
            Otherwise returns None and lists sessions that need re-analysis.
        """
        if not entries:
            return None, []

        # Build chain signature
        chain_signature = _build_chain_signature(entries)
        if not chain_signature:
            return None, []

        # Get current/origin session (last in oldest-to-newest order)
        current_entry = entries[-1]
        current_session_id = (
            getattr(current_entry, "session_id", None)
            or current_entry.get("sessionId", "")
        )
        if not current_session_id:
            return None, []

        # Check cache for current session (origin of the chain result)
        current_cache = _load_session_cache(current_session_id)
        if current_cache is None:
            self._cache_misses += 1
            return None, [current_session_id]

        # Verify chain signature matches
        if current_cache.chain_signature != chain_signature:
            self._cache_misses += 1
            return None, [current_session_id]

        # CRITICAL FIX: validate origin session's own mtime
        # (was previously only checked for non-origin sessions)
        origin_transcript_path = (
            getattr(current_entry, "transcript_path", None)
            or current_entry.get("transcriptPath")
        )
        if origin_transcript_path:
            origin_mtime = _get_session_mtime(Path(origin_transcript_path))
            if origin_mtime is None or origin_mtime != current_cache.mtime:
                self._cache_misses += 1
                return None, [current_session_id]
        else:
            # No path to validate — treat as potential staleness
            self._cache_misses += 1
            return None, [current_session_id]

        # Verify all sessions have valid mtime in cache
        # Collect non-origin entries that need cache loading
        entries_to_check: list[tuple[str, dict]] = []
        for entry in entries:
            sid = getattr(entry, "session_id", None) or entry.get("sessionId", "")
            if not sid or sid == current_session_id:
                continue
            entries_to_check.append((sid, entry))

        # Parallel cache loading via ThreadPoolExecutor
        cached_results: dict[str, CachedSessionAnalysis | None] = {}
        if entries_to_check:
            with ThreadPoolExecutor(max_workers=min(len(entries_to_check), 8)) as executor:
                future_to_sid = {
                    executor.submit(_load_session_cache, sid): sid
                    for sid, _ in entries_to_check
                }
                for future in as_completed(future_to_sid):
                    sid = future_to_sid[future]
                    try:
                        cached_results[sid] = future.result()
                    except Exception:
                        cached_results[sid] = None

        # Validate all cached results
        missed_sessions: set[str] = set()
        for sid, entry in entries_to_check:
            cache = cached_results.get(sid)
            if cache is None:
                missed_sessions.add(sid)
                continue

            # Get current mtime
            transcript_path = getattr(entry, "transcript_path", None) or entry.get("transcriptPath")
            if not transcript_path:
                # Missing transcript_path: cannot verify integrity — treat as cache miss
                missed_sessions.add(sid)
                continue

            current_mtime = _get_session_mtime(Path(transcript_path))
            if current_mtime is None or current_mtime != cache.mtime:
                missed_sessions.add(sid)
                continue

            # Also verify chain signature in each session's cache matches current
            if cache.chain_signature != chain_signature:
                missed_sessions.add(sid)

        if missed_sessions:
            self._cache_misses += len(missed_sessions)
            return None, list(missed_sessions)

        # CRITICAL FIX: Re-validate origin session mtime just before returning
        # to prevent TOCTOU vulnerability between initial validation and use
        if origin_transcript_path:
            final_origin_mtime = _get_session_mtime(Path(origin_transcript_path))
            if final_origin_mtime is None or final_origin_mtime != current_cache.mtime:
                self._cache_misses += 1
                logger.debug("Origin session mtime changed after initial validation - cache miss")
                return None, [current_session_id]

        # All sessions cached and mtimes match — return cached result
        self._cache_hits += 1
        logger.info(
            "Session memoizer cache HIT for chain %s (%d sessions)",
            chain_signature[:40],
            len(entries),
        )
        return current_cache.result, []

    def cache_session_result(
        self,
        session_id: str,
        transcript_path: Path,
        chain_depth: int,
        chain_signature: str,
        result: dict[str, Any],
    ) -> None:
        """Cache the analysis result for a session."""
        mtime = _get_session_mtime(transcript_path)
        if mtime is None:
            logger.warning("Cannot cache result for session %s: transcript not found", session_id)
            return
        _save_session_cache(
            session_id=session_id,
            transcript_path=transcript_path,
            mtime=mtime,
            chain_depth=chain_depth,
            chain_signature=chain_signature,
            result=result,
        )

    def get_cache_stats(self) -> dict[str, int]:
        """Return cache hit/miss statistics."""
        return {"hits": self._cache_hits, "misses": self._cache_misses}

    def clear_cache(self, session_id: str | None = None) -> None:
        """Clear cache for a specific session, or all sessions if None."""
        if session_id:
            cache_path = _get_session_cache_path(session_id)
            try:
                cache_path.unlink(missing_ok=True)
                logger.info("Cleared cache for session %s", session_id)
            except OSError as e:
                logger.warning("Failed to clear cache for %s: %s", session_id, e)
        else:
            cache_dir = _get_sessions_cache_dir()
            if cache_dir.exists():
                for cache_file in cache_dir.glob("*.json"):
                    try:
                        cache_file.unlink()
                    except OSError:
                        pass
                logger.info("Cleared all session caches")
