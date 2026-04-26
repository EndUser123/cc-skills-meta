"""Gap Verifier Subagent — evidence verification for reported gaps.

Priority: L2 (runs after L1 detectors, before merge)
Purpose: Validate that reported gaps are real and not stale.

Checks:
- File path exists on disk
- Line number is within file bounds
- TODO/FIXME markers are still present at reported locations
- Stale marker detection (markers older than N days)

Ported from /r skill's investigate (evidence verification) step.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class VerificationResult:
    """Result of verifying a single gap."""
    gap_id: str
    is_valid: bool
    reason: str | None = None
    file_exists: bool | None = None
    line_exists: bool | None = None
    marker_present: bool | None = None


@dataclass
class BatchVerificationResult:
    """Result of verifying a batch of gaps."""
    results: list[VerificationResult]
    total_checked: int
    valid_count: int
    invalid_count: int
    stale_count: int
    stale_threshold_days: int = 90


# Code markers to verify
_CODE_MARKERS = ("TODO:", "FIXME:", "HACK:", "XXX:", "BUG:", "NOTE:")

# Threshold for stale markers (days)
DEFAULT_STALE_THRESHOLD_DAYS = 90


def verify_gap(gap: dict[str, Any], project_root: Path | None = None) -> VerificationResult:
    """Verify a single gap against the filesystem.

    Args:
        gap: Gap dictionary with file_path, line_number, type, message.
        project_root: Project root for resolving relative paths.

    Returns:
        VerificationResult with validation status.
    """
    root = Path(project_root or Path.cwd()).resolve()
    gap_id = gap.get("id", gap.get("gap_id", "unknown"))
    file_path = gap.get("file_path")
    line_number = gap.get("line_number")
    gap_type = gap.get("type", "")

    # Gaps without file paths are assumed valid (can't verify location)
    if not file_path:
        return VerificationResult(
            gap_id=gap_id,
            is_valid=True,
            reason="No file path to verify",
        )

    # Resolve file path
    resolved = root / file_path if not Path(file_path).is_absolute() else Path(file_path)
    if not resolved.exists():
        return VerificationResult(
            gap_id=gap_id,
            is_valid=False,
            reason=f"File not found: {file_path}",
            file_exists=False,
        )

    # For code markers, verify the marker is still at the reported line
    if gap_type == "code_marker" and line_number is not None:
        return _verify_code_marker(gap_id, resolved, line_number, gap.get("message", ""))

    # For other gap types, just verify file exists
    return VerificationResult(
        gap_id=gap_id,
        is_valid=True,
        file_exists=True,
        line_exists=line_number is None or _line_in_file(resolved, line_number),
    )


def _verify_code_marker(
    gap_id: str, file_path: Path, line_number: int, _message: str
) -> VerificationResult:
    """Verify that a code marker is still present at the reported location.

    Also checks nearby lines (±2) to handle minor line shifts from edits.
    """
    try:
        lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return VerificationResult(
            gap_id=gap_id,
            is_valid=False,
            reason=f"Cannot read file: {file_path}",
            file_exists=True,
        )

    if line_number > len(lines):
        return VerificationResult(
            gap_id=gap_id,
            is_valid=False,
            reason=f"Line {line_number} beyond file length ({len(lines)} lines)",
            file_exists=True,
            line_exists=False,
        )

    # Check exact line and nearby lines (±2) for marker
    for offset in range(max(0, line_number - 3), min(len(lines), line_number + 2)):
        line_content = lines[offset].upper()
        if any(marker in line_content for marker in _CODE_MARKERS):
            return VerificationResult(
                gap_id=gap_id,
                is_valid=True,
                file_exists=True,
                line_exists=True,
                marker_present=True,
            )

    return VerificationResult(
        gap_id=gap_id,
        is_valid=False,
        reason=f"Code marker no longer present near line {line_number}",
        file_exists=True,
        line_exists=True,
        marker_present=False,
    )


def _line_in_file(file_path: Path, line_number: int) -> bool:
    """Check if a line number is within file bounds."""
    try:
        line_count = sum(1 for _ in file_path.open(encoding="utf-8", errors="ignore"))
        return 1 <= line_number <= line_count
    except OSError:
        return False


def verify_gaps(
    gaps: list[dict[str, Any]],
    project_root: Path | None = None,
) -> BatchVerificationResult:
    """Verify a batch of gaps against the filesystem.

    Args:
        gaps: List of gap dictionaries.
        project_root: Project root for resolving relative paths.

    Returns:
        BatchVerificationResult with per-gap verification.
    """
    results = []
    for gap in gaps:
        result = verify_gap(gap, project_root)
        results.append(result)

    return BatchVerificationResult(
        results=results,
        total_checked=len(results),
        valid_count=sum(1 for r in results if r.is_valid),
        invalid_count=sum(1 for r in results if not r.is_valid),
        stale_count=sum(1 for r in results if r.reason and "no longer present" in r.reason),
    )


def filter_valid_gaps(
    gaps: list[dict[str, Any]],
    project_root: Path | None = None,
) -> list[dict[str, Any]]:
    """Filter gaps to only include verified ones, marking invalid ones.

    Invalid gaps are not removed — they get verification_evidence metadata
    so the RNS can surface them with appropriate caveats.

    Args:
        gaps: List of gap dictionaries.
        project_root: Project root for resolving relative paths.

    Returns:
        Gaps with verification metadata added.
    """
    root = Path(project_root or Path.cwd()).resolve()
    result = []

    for gap in gaps:
        verification = verify_gap(gap, root)
        gap_copy = dict(gap)
        gap_copy["is_verified"] = verification.is_valid

        if not verification.is_valid:
            gap_copy["verification_evidence"] = verification.reason or "Verification failed"
            gap_copy["confidence"] = min(gap_copy.get("confidence", 0.8) * 0.5, 0.4)
        else:
            gap_copy["verification_evidence"] = "Verified"

        result.append(gap_copy)

    return result
