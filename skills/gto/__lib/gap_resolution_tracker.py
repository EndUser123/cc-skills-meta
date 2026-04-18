"""Gap Resolution Tracker - Track which skills resolved which gaps across GTO runs.

Priority: P1 (runs during gap detection, before skill coverage recommendation)

Purpose:
  When GTO re-runs on the same target, diff current gaps against the previous run.
  Gaps that were present before but are absent now were "resolved" by whatever
  skill ran in between. Credit that skill in the coverage log so future
  skill recommendations are smarter (don't re-recommend a skill that consistently
  fails to resolve a given gap type).

Mechanism:
  - On each GTO run, before producing gaps, load the "previous gaps" snapshot
    for this target from the state directory.
  - After producing current gaps, compute the diff:
      resolved_gaps = prev_gaps - current_gaps  (by gap_id)
      new_gaps     = current_gaps - prev_gaps  (by gap_id)
  - For resolved_gaps: look up the most recent skill coverage entry for this
    target (from skill_coverage log). If one exists, append a "resolution"
    record noting which gap_ids that skill resolved.
  - Save the current gaps snapshot for use in the next run.
  - When detect_skill_coverage() runs, it reads resolution history to
    weight skill recommendations (skills that resolved similar gaps before
    get boosted; skills that consistently fail get demoted).

Resolution log format (~/.claude/.evidence/skill_coverage/{target}-resolutions.jsonl):
    {"skill": "/critique", "gap_ids_resolved": ["TEST-001", "DOC-002"],
     "gap_types_resolved": ["test_gap", "missing_docs"], "timestamp": "..."}

No TTL: Freshness determined by git state - if target changed since last run,
resolution history may be stale (but still useful signal).
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Cross-platform file locking
try:
    import fcntl

    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

# Windows file locking
try:
    import msvcrt

    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False

logger = logging.getLogger(__name__)

# ── Effectiveness scoring constants ──────────────────────────────────────────
# Used by get_skill_effectiveness_score()

_FAILURE_DEMOTION_PER_FAILED = 0.05
_FAILURE_DEMOTION_CAP = 0.3
_VERIFICATION_BOOST_PER_VERIFIED = 0.1
_VERIFICATION_BOOST_CAP = 0.2

# ── Gap ID normalization ───────────────────────────────────────────────────────


def _normalize_gap_key(gap_id: str) -> str:
    """Normalize a gap ID for comparison across runs.

    Gap IDs may contain ephemeral components (timestamps, run-specific suffixes).
    This strips those to get the semantic gap type.

    Example: "TEST-001" -> "TEST-001"
            "SESSION-unco-001" -> "SESSION-unco"
    """
    # Strip trailing numeric suffixes used for uniqueness within a run.
    # Only strip when the base (before the trailing numeric suffix) itself
    # contains a hyphen — meaning it already has an ephemeral suffix.
    # "TEST-001" (base="TEST", no hyphen) → keep as-is (semantic ID)
    # "TEST-001-1" (base="TEST-001", has hyphen) → strip to "TEST-001"
    # "SESSION-abc-003" (base="SESSION-abc", has hyphen) → strip to "SESSION-abc"
    # "DOC-gap-003" (base="DOC-gap", has hyphen) → strip to "DOC-gap"
    parts = gap_id.rsplit("-", 1)
    if len(parts) == 2 and parts[1].isdigit() and "-" in parts[0]:
        return parts[0]
    return gap_id


def _extract_gap_type(gap_id: str) -> str:
    """Extract the semantic gap type from a gap ID.

    Example: "TEST-001" -> "test_gap"
             "DOC-gap-003" -> "doc_gap"
             "SESSION-unco-001" -> "session_outcome_unco"
    """
    normalized = _normalize_gap_key(gap_id)
    # Remove the numeric suffix then extract type from remaining segments
    parts = normalized.rsplit("-", 1)
    # Preserve both segments (e.g. "SESSION-unco" -> "session_unco", not "session")
    type_str = "_".join(parts) if len(parts) == 2 else normalized
    return type_str.lower().replace("-", "_")


def _extract_root_type(gap_type: str) -> str:
    """Extract root type from full normalized gap type.

    This converts full gap types (e.g., "test_gap", "missing_docs") to root types
    (e.g., "test", "docs") for matching against user-supplied gap type sets.

    Examples:
        "test_gap" -> "test"
        "missing_docs" -> "docs"
        "doc_gap" -> "doc"
        "contract_gap" -> "contract"
        "code_quality" -> "quality"
    """
    # Remove common suffixes
    for suffix in ["_gap", "_failure", "_issue", "_error"]:
        if gap_type.endswith(suffix):
            return gap_type[:-len(suffix)]
    # Remove common prefixes
    for prefix in ["missing_", "outdated_", "deprecated_"]:
        if gap_type.startswith(prefix):
            return gap_type[len(prefix):]
    # Fallback: return as-is or first component before underscore
    parts = gap_type.split("_")
    return parts[0] if len(parts) > 1 else gap_type


# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass
class ResolutionRecord:
    """A single resolution event — a skill resolved one or more gaps."""

    skill: str
    gap_ids_resolved: list[str]
    gap_types_resolved: list[str]
    timestamp: str
    terminal_id: str | None = None
    verified: bool = False  # True once verified (gap stayed resolved)
    verified_at: str | None = None  # ISO timestamp when verified


@dataclass
class ResolutionVerificationRecord:
    """Result of verifying a past resolution — did the gap stay resolved?"""

    skill: str
    gap_ids: list[str]
    gap_types: list[str]
    resolution_timestamp: str
    verification_timestamp: str
    status: str  # "verified" (still absent) | "failed" (reappeared)
    reason: str  # "gap_still_absent" | "gap_reappeared"
    terminal_id: str | None = None


@dataclass
class ResolutionResult:
    """Result of tracking gap resolutions."""

    resolved_count: int
    new_count: int
    persistent_count: int  # Gaps present in both runs
    verified_count: int = 0  # Resolutions verified still-absent this run
    failed_count: int = 0  # Resolutions that reappeared this run
    resolved_gap_ids: list[str] = field(default_factory=list)
    new_gap_ids: list[str] = field(default_factory=list)
    credited_skill: str | None = None


# ── Path helpers ─────────────────────────────────────────────────────────────


def _get_resolution_log_path(target_key: str) -> Path:
    """Get path to resolution log for a target."""
    sanitized = re.sub(r"[^\w\-.]", "_", target_key)
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    return Path.home() / ".evidence" / "skill_coverage" / f"{sanitized}-resolutions.jsonl"


def _get_verification_log_path(target_key: str) -> Path:
    """Get path to resolution verification log for a target."""
    sanitized = re.sub(r"[^\w\-.]", "_", target_key)
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    return Path.home() / ".evidence" / "skill_coverage" / f"{sanitized}-verifications.jsonl"


def _get_previous_gaps_path(target_key: str, terminal_id: str) -> Path:
    """Get path to previous gaps snapshot for a target+terminal."""
    sanitized = re.sub(r"[^\w\-.]", "_", target_key)
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    return (
        Path.home() / ".evidence" / "gto-state" / f"{terminal_id}" / f"{sanitized}-prev-gaps.json"
    )


# ── Core functions ────────────────────────────────────────────────────────────


def _load_previous_gaps(prev_path: Path) -> dict[str, Any] | None:
    """Load previous gaps snapshot if it exists."""
    if not prev_path.exists():
        return None
    try:
        with open(prev_path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _save_previous_gaps(
    prev_path: Path,
    gaps: list[dict[str, Any]],
    terminal_id: str,
) -> None:
    """Save current gaps as the 'previous' snapshot for the next run."""
    try:
        prev_path.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write
        tmp = prev_path.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(
                {
                    "gaps": gaps,
                    "terminal_id": terminal_id,
                    "timestamp": datetime.now().isoformat(),
                },
                f,
            )
        tmp.replace(prev_path)
    except OSError:
        pass  # Non-critical


def _read_resolution_log(log_path: Path) -> list[ResolutionRecord]:
    """Read all resolution records from the log."""
    records = []
    if not log_path.exists():
        return records
    try:
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    records.append(
                        ResolutionRecord(
                            skill=data.get("skill", ""),
                            gap_ids_resolved=data.get("gap_ids_resolved", []),
                            gap_types_resolved=data.get("gap_types_resolved", []),
                            timestamp=data.get("timestamp", ""),
                            terminal_id=data.get("terminal_id"),
                            verified=data.get("verified", False),
                            verified_at=data.get("verified_at"),
                        )
                    )
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return records


def _read_skill_coverage_log(target_key: str) -> list[dict[str, Any]]:
    """Read most recent skill coverage entry for a target."""
    from .skill_coverage_detector import _get_skill_coverage_path

    coverage_path = _get_skill_coverage_path(target_key)
    if not coverage_path.exists():
        return []
    try:
        with open(coverage_path) as f:
            lines = f.readlines()
        if not lines:
            return []
        # Return all entries (most recent last after sort by mtime)
        entries = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries
    except OSError:
        return []


def _append_resolution_record(
    target_key: str,
    record: ResolutionRecord,
) -> None:
    """Append a resolution record to the log."""
    log_path = _get_resolution_log_path(target_key)
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a") as f:
            f.write(json.dumps(record.__dict__) + "\n")
    except OSError:
        pass


def _read_verification_log(log_path: Path) -> list[ResolutionVerificationRecord]:
    """Read verification records from the log."""
    records = []
    if not log_path.exists():
        return records
    try:
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    records.append(
                        ResolutionVerificationRecord(
                            skill=data.get("skill", ""),
                            gap_ids=data.get("gap_ids", []),
                            gap_types=data.get("gap_types", []),
                            resolution_timestamp=data.get("resolution_timestamp", ""),
                            verification_timestamp=data.get("verification_timestamp", ""),
                            status=data.get("status", ""),
                            reason=data.get("reason", ""),
                            terminal_id=data.get("terminal_id"),
                        )
                    )
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return records


def _append_verification_record(
    target_key: str,
    record: ResolutionVerificationRecord,
) -> None:
    """Append a verification record to the log."""
    log_path = _get_verification_log_path(target_key)
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a") as f:
            f.write(json.dumps(record.__dict__) + "\n")
    except OSError:
        pass


def _get_verified_gap_ids(log_path: Path) -> set[str]:
    """Get the set of gap IDs that have already been verified (from any resolution)."""
    verified_records = _read_verification_log(log_path)
    verified = set()
    for rec in verified_records:
        for gid in rec.gap_ids:
            verified.add(_normalize_gap_key(gid))
    return verified


def _verify_past_resolutions(
    target_key: str,
    current_gap_ids: set[str],
    terminal_id: str,
) -> tuple[int, int]:
    """Verify whether previously-resolved gaps stayed resolved.

    For each unverified resolution record in the log:
    - If the resolved gap is STILL absent from current_gap_ids → VERIFIED
    - If the resolved gap has REAPPEARED in current_gap_ids → FAILED

    This is the "loop closure" mechanism: it confirms that a credited
    resolution actually held by checking in the next GTO run.

    Args:
        target_key: Target identifier
        current_gap_ids: Set of gap IDs currently present
        terminal_id: Terminal ID for this run

    Returns:
        Tuple of (verified_count, failed_count)
    """
    log_path = _get_resolution_log_path(target_key)
    verification_log_path = _get_verification_log_path(target_key)
    lock_path = verification_log_path.parent / ".verification.lock"

    # Lock file for exclusive access to verification log
    lock_file_obj = None
    try:
        # Open lock file
        lock_file_obj = open(lock_path, "w")

        # Acquire lock
        if HAS_FCNTL:
            fcntl.flock(lock_file_obj.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        elif HAS_MSVCRT:
            msvcrt.locking(lock_file_obj.fileno(), msvcrt.LK_NBLCK, 1)

        # Lock acquired — read and write verification log
        records = _read_resolution_log(log_path)
        verified_gap_ids = _get_verified_gap_ids(verification_log_path)

        verified_count = 0
        failed_count = 0
        now = datetime.now().isoformat()

        for record in records:
            # Skip already-verified records (by checking if any of their gap IDs were verified)
            record_gap_ids = {_normalize_gap_key(gid) for gid in record.gap_ids_resolved}
            already_verified = record_gap_ids & verified_gap_ids

            # Only verify gaps we haven't verified yet
            unverified_gap_ids = record_gap_ids - already_verified

            if not unverified_gap_ids:
                continue

            # Check each unverified gap
            for gap_id in unverified_gap_ids:
                normalized = _normalize_gap_key(gap_id)
                if normalized in current_gap_ids:
                    # Gap reappeared → resolution FAILED
                    status = "failed"
                    reason = "gap_reappeared"
                    failed_count += 1
                else:
                    # Gap still absent → resolution VERIFIED
                    status = "verified"
                    reason = "gap_still_absent"
                    verified_count += 1

                # Append verification record
                verification = ResolutionVerificationRecord(
                    skill=record.skill,
                    gap_ids=[_normalize_gap_key(gap_id)],
                    gap_types=record.gap_types_resolved,
                    resolution_timestamp=record.timestamp,
                    verification_timestamp=now,
                    status=status,
                    reason=reason,
                    terminal_id=terminal_id,
                )
                _append_verification_record(target_key, verification)

        return verified_count, failed_count
    except (OSError, IOError):
        # Lock busy or unavailable — fail closed, do NOT write unprotected
        raise
    finally:
        # Always release lock if it was acquired
        if lock_file_obj is not None:
            try:
                if HAS_FCNTL:
                    fcntl.flock(lock_file_obj.fileno(), fcntl.LOCK_UN)
                elif HAS_MSVCRT:
                    msvcrt.locking(lock_file_obj.fileno(), msvcrt.LK_UNLCK, 1)
            except (OSError, IOError):
                # Ignore errors during lock release
                pass
            lock_file_obj.close()


# ── Public API ─────────────────────────────────────────────────────────────────


def track_gap_resolutions(
    current_gaps: list[dict[str, Any]],
    target_key: str,
    terminal_id: str,
    project_root: Path | None = None,  # noqa: ARG001
) -> ResolutionResult:
    """Track which gaps were resolved since the last GTO run.

    Computes the diff between current gaps and the previous snapshot.
    When gaps disappeared, credits the most recently-run skill on that target.

    Args:
        current_gaps: List of gap dicts from the current GTO run
        target_key: Target identifier (path relative to project root)
        terminal_id: Terminal ID for state isolation
        project_root: Project root (unused, for API compatibility)

    Returns:
        ResolutionResult with diff stats and any skill credited
    """
    # Load previous gaps snapshot
    prev_path = _get_previous_gaps_path(target_key, terminal_id)
    prev_data = _load_previous_gaps(prev_path)
    prev_gaps: list[dict[str, Any]] = prev_data.get("gaps", []) if prev_data else []

    prev_ids = {_normalize_gap_key(g["id"]) for g in prev_gaps if g.get("id") is not None}
    curr_ids = {_normalize_gap_key(g["id"]) for g in current_gaps if g.get("id") is not None}

    # Verify past resolutions: check if previously-credited gaps stayed resolved
    verified_count, failed_count = _verify_past_resolutions(target_key, curr_ids, terminal_id)

    resolved_ids = prev_ids - curr_ids
    new_ids = curr_ids - prev_ids

    resolved_gap_ids = sorted(resolved_ids)
    new_gap_ids = sorted(new_ids)

    result = ResolutionResult(
        resolved_count=len(resolved_gap_ids),
        new_count=len(new_gap_ids),
        persistent_count=len(prev_ids & curr_ids),
        verified_count=verified_count,
        failed_count=failed_count,
        resolved_gap_ids=resolved_gap_ids,
        new_gap_ids=new_gap_ids,
    )

    # If gaps were resolved, look up which skill most recently ran on this target
    if resolved_gap_ids:
        coverage_entries = _read_skill_coverage_log(target_key)
        if coverage_entries:
            # Most recent entry is last in file (append-only)
            most_recent = coverage_entries[-1]
            skill = most_recent.get("skill", "")
            if skill:
                result.credited_skill = skill
                # Extract gap types from resolved gaps
                prev_gap_map = {_normalize_gap_key(g["id"]): g for g in prev_gaps}
                types_resolved = sorted(
                    {_extract_gap_type(gid) for gid in resolved_gap_ids if gid in prev_gap_map}
                )
                record = ResolutionRecord(
                    skill=skill,
                    gap_ids_resolved=resolved_gap_ids,
                    gap_types_resolved=types_resolved,
                    timestamp=datetime.now().isoformat(),
                    terminal_id=terminal_id,
                )
                _append_resolution_record(target_key, record)

    # Save current gaps as the new snapshot
    _save_previous_gaps(prev_path, current_gaps, terminal_id)

    return result


def get_skill_resolution_history(
    target_key: str,
    skill: str | None = None,
    limit: int = 20,
) -> list[ResolutionRecord]:
    """Get resolution history for a target, optionally filtered by skill.

    Args:
        target_key: Target identifier
        skill: If provided, only return records for this skill
        limit: Maximum records to return (most recent first)

    Returns:
        List of ResolutionRecord objects
    """
    log_path = _get_resolution_log_path(target_key)
    all_records = _read_resolution_log(log_path)

    if skill:
        all_records = [r for r in all_records if r.skill == skill]

    # Return most recent first
    return list(reversed(all_records[-limit:]))


def get_skill_effectiveness_score(
    target_key: str,
    skill: str,
    gap_types: list[str],
) -> float:
    """Compute an effectiveness score for a skill against given gap types.

    Score range:
      1.0  = skill resolved these gap types on every recent run
      0.5  = mixed results
      0.0  = skill has never resolved these gap types or gaps reappeared

    This factors in loop-closure verification: skills that were credited with
    resolving a gap but the gap later reappeared get demoted.

    Args:
        target_key: Target identifier
        skill: Skill name (e.g., "/critique")
        gap_types: List of gap type strings (e.g., ["test_gap", "missing_docs"])

    Returns:
        Effectiveness score 0.0 to 1.0
    """
    gap_type_set = set(gap_types)

    # Get resolution history
    history = get_skill_resolution_history(target_key, skill=skill, limit=50)

    # Get verification history for demotion signal
    verification_log_path = _get_verification_log_path(target_key)
    verifications = _read_verification_log(verification_log_path)

    # Filter verifications for this skill and relevant gap types
    skill_verifications = [
        v
        for v in verifications
        if v.skill == skill and any(gt in gap_type_set or _extract_root_type(gt) in gap_type_set for gt in v.gap_types)
    ]

    verified_count = sum(1 for v in skill_verifications if v.status == "verified")
    failed_count = sum(1 for v in skill_verifications if v.status == "failed")

    if not history and not skill_verifications:
        return 0.5  # No history = unknown, neutral score

    # Count resolution attempts (each record = one run where this skill was used)
    total_attempts = len(history)
    if total_attempts == 0:
        total_attempts = 1

    # Successful resolutions: relevant gap types resolved and stayed absent
    successful_resolutions = 0
    for record in history:
        for gt in record.gap_types_resolved:
            if _extract_root_type(gt) in gap_type_set:
                successful_resolutions += 1

    # Base score from resolution success rate
    base_score = successful_resolutions / total_attempts if total_attempts > 0 else 0.0

    # Demotion factor from failed verifications (gap reappeared after being credited)
    failure_demotion = min(failed_count * _FAILURE_DEMOTION_PER_FAILED, _FAILURE_DEMOTION_CAP)

    # Boost from verified resolutions (gap stayed absent)
    verification_boost = min(verified_count * _VERIFICATION_BOOST_PER_VERIFIED, _VERIFICATION_BOOST_CAP)

    final_score = base_score + verification_boost - failure_demotion
    return min(max(final_score, 0.0), 1.0)


@dataclass
class GapDecayMetrics:
    """Metrics for gap-type recurrence patterns."""
    gap_type: str
    occurrences: int
    first_seen: str | None
    last_seen: str | None
    days_span: float | None
    verified_count: int
    failed_count: int


def get_gap_decay_metrics(target_key: str) -> dict[str, GapDecayMetrics]:
    """
    Compute per-gap-type recurrence metrics from resolution log.

    Only gap types with 2+ occurrences are included — a single occurrence
    provides no recurrence signal.
    """
    log_path = _get_resolution_log_path(target_key)
    if not log_path.exists():
        return {}

    records = _read_resolution_log(log_path)
    if not records:
        return {}

    by_type: dict[str, list[ResolutionRecord]] = {}
    for rec in records:
        for gap_type in rec.gap_types_resolved:
            norm = _normalize_gap_key(gap_type)
            by_type.setdefault(norm, []).append(rec)

    metrics: dict[str, GapDecayMetrics] = {}
    for gap_type, recs in by_type.items():
        if len(recs) < 2:
            continue

        timestamps = [r.timestamp for r in recs if r.timestamp]
        verified_count = sum(1 for r in recs if r.verified)
        failed_count = len(recs) - verified_count

        from datetime import datetime
        first_ts: str | None = min(timestamps) if timestamps else None
        last_ts: str | None = max(timestamps) if timestamps else None

        days_span: float | None = None
        if first_ts and last_ts:
            try:
                # Normalize all ISO 8601 timezone formats before parsing
                # Handles: Z, +00:00, +00, +0530, -08:00, -0800, etc.
                import re

                def _normalize_ts(ts: str) -> str:
                    if ts.endswith("Z"):
                        return ts[:-1] + "+00:00"
                    # Match +/-HH:MM, +/-HHMM, +/-HH
                    m = re.match(r"^(.+?)([+-])(\d{2}):?(\d{2})?$", ts)
                    if m:
                        sign = m.group(2)
                        hh = m.group(3)
                        mm = m.group(4) or "00"
                        return f"{m.group(1)}{sign}{hh}:{mm}"
                    return ts

                first_dt = datetime.fromisoformat(_normalize_ts(first_ts))
                last_dt = datetime.fromisoformat(_normalize_ts(last_ts))
                days_span = (last_dt - first_dt).total_seconds() / 86400.0
            except (ValueError, OSError):
                pass

        metrics[gap_type] = GapDecayMetrics(
            gap_type=gap_type,
            occurrences=len(recs),
            first_seen=first_ts,
            last_seen=last_ts,
            days_span=days_span,
            verified_count=verified_count,
            failed_count=failed_count,
        )

    return metrics
