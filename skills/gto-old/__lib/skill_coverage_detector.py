"""SkillCoverageDetector - Detect skill coverage and suggest relevant skills.

Priority: P1 (runs during RNS formatting, not gap detection)
Purpose: Suggest relevant skills based on:
  1. Actual gap findings (gap-aware recommendations)
  2. Project type heuristics (fallback when no gaps)

This is NOT a gap detector - it's a skill routing layer that:
- Analyzes GTO gap findings to recommend contextually relevant skills
- Consults the skill registry for rich skill metadata
- Falls back to project type heuristics when no gaps are provided

Skill coverage log format (~/.claude/.evidence/skill_coverage/{target}.jsonl):
    {"skill": "/critique", "target": "skills/usm", "terminal_id": "...", "timestamp": "...", "git_sha": "..."}

No TTL: Freshness determined by git state - if target changed since last run, coverage is stale.
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .gap_resolution_tracker import get_skill_effectiveness_score
from .gap_skill_mapper import (
    format_recommendations_for_rsn,
    generate_skill_recommendations,
    inject_skill_context_for_gaps,
)

# Import changelog reader — shared utility for skill activity tracking
# __lib at skills level is added to sys.path, use direct import
import sys
from pathlib import Path as _Path

_lib_path = _Path(__file__).parent.parent.parent / "__lib" / "changelog_writer.py"
if _lib_path.exists():
    _lib_dir = str(_lib_path.parent)
    if _lib_dir not in sys.path:
        sys.path.insert(0, _lib_dir)
    try:
        from changelog_writer import get_skills_run as _get_changelog_skills
    except ImportError:
        _get_changelog_skills = None
else:
    _get_changelog_skills = None

logger = logging.getLogger(__name__)

# Project type → relevant skills mapping (fallback when no gaps provided)
PROJECT_TYPE_SKILLS: list[dict] = [
    {
        "type": "python_no_tests",
        "patterns": [("*.py", None)],  # (pattern, must_exist_dir)
        "negative_patterns": [("tests", True), ("test", True)],
        "suggestion": "/tdd",
        "reason": "Python project detected but no test directory found",
    },
    {
        "type": "hooks_project",
        "patterns": [("hooks/**/*.py", None)],
        "negative_patterns": [],
        "suggestion": "/critique",
        "reason": "Hooks project detected - audit for behavioral compliance",
    },
    {
        "type": "skills_project",
        "patterns": [("**/SKILL.md", None)],
        "negative_patterns": [],
        "suggestion": "/critique",
        "reason": "Skills project detected - use critique for quality review",
    },
    {
        "type": "python_scripts",
        "patterns": [("scripts/**/*.py", None), ("**/*.py", None)],
        "negative_patterns": [],
        "suggestion": "/tdd",
        "reason": "Python scripts detected - consider test-driven development",
    },
]


@dataclass
class SkillCoverageEntry:
    """Single entry in the skill coverage log."""

    skill: str
    target: str
    terminal_id: str
    timestamp: str
    git_sha: str | None = None
    gap_ids_targeted: list[str] = field(default_factory=list)


@dataclass
class SkillSuggestion:
    """A suggested skill based on project type."""

    skill: str
    reason: str
    priority: str = "LOW"  # Skill suggestions are informational, not critical


@dataclass
class SkillCoverageResult:
    """Result of skill coverage detection."""

    suggestions: list[SkillSuggestion] = field(default_factory=list)
    coverage_log_exists: bool = False
    skills_already_run: list[str] = field(default_factory=list)
    target_key: str = ""


def _sanitize_target_key(target: str) -> str:
    """Sanitize target path for use as filename.

    Args:
        target: Target path relative to project root

    Returns:
        Sanitized string safe for use as filename
    """
    # Replace path separators and special chars
    sanitized = re.sub(r"[^\w\-.]", "_", target)
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    return sanitized


def _get_skill_coverage_path(target_key: str) -> Path:
    """Get path to skill coverage log for a target.

    Args:
        target_key: Target key (path relative to project root)

    Returns:
        Path to the JSONL coverage log
    """
    sanitized = _sanitize_target_key(target_key)
    return Path.home() / ".evidence" / "skill_coverage" / f"{sanitized}.jsonl"


def _read_skill_coverage_log(coverage_path: Path) -> list[SkillCoverageEntry]:
    """Read skill coverage log entries.

    Args:
        coverage_path: Path to the JSONL coverage log

    Returns:
        List of SkillCoverageEntry objects
    """
    entries = []
    if not coverage_path.exists():
        return entries

    try:
        with open(coverage_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    entries.append(
                        SkillCoverageEntry(
                            skill=data.get("skill", ""),
                            target=data.get("target", ""),
                            terminal_id=data.get("terminal_id", ""),
                            timestamp=data.get("timestamp", ""),
                            git_sha=data.get("git_sha"),
                            gap_ids_targeted=data.get("gap_ids_targeted", []),
                        )
                    )
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass

    return entries


def _rotate_skill_coverage_log(coverage_path: Path) -> None:
    """Rotate skill coverage log if it exceeds 1MB.

    Keeps the last 100 entries to prevent unbounded growth.

    Args:
        coverage_path: Path to the JSONL coverage log
    """
    try:
        # Read all existing entries
        entries = []
        with open(coverage_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        # Keep only the last 100 entries
        if len(entries) > 100:
            entries = entries[-100:]
        else:
            return  # No rotation needed

        # Write to temp file then rename (atomic-ish on Windows, atomic on POSIX)
        import tempfile as _tf
        tmp_fd, tmp_path = _tf.mkstemp(
            dir=str(coverage_path.parent), suffix=".jsonl.tmp"
        )
        try:
            with open(tmp_fd, "w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")
            Path(tmp_path).replace(coverage_path)
        except BaseException:
            import os as _os
            _os.unlink(tmp_path)
            raise
    except OSError:
        # If rotation fails, leave the file as-is
        pass


def _append_skill_coverage(
    target_key: str,
    skill: str,
    terminal_id: str,
    git_sha: str | None = None,
    gap_ids_targeted: list[str] | None = None,
) -> bool:
    """Append a skill coverage entry to the log.

    Args:
        target_key: Target key (path relative to project_root)
        skill: Skill that was run (e.g., "/critique")
        terminal_id: Terminal identifier for the session
        git_sha: Optional git SHA at time of skill run
        gap_ids_targeted: Optional list of gap IDs this skill intended to address

    Returns:
        True if entry was appended successfully, False otherwise
    """
    coverage_path = _get_skill_coverage_path(target_key)

    # Ensure parent directory exists
    try:
        coverage_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return False

    entry = SkillCoverageEntry(
        skill=skill,
        target=target_key,
        terminal_id=terminal_id,
        timestamp=datetime.now().isoformat(),
        git_sha=git_sha,
        gap_ids_targeted=gap_ids_targeted or [],
    )

    try:
        # Check file size for rotation (>1MB threshold)
        if coverage_path.exists():
            try:
                file_size = coverage_path.stat().st_size
                if file_size > 1024 * 1024:  # 1MB
                    _rotate_skill_coverage_log(coverage_path)
            except OSError:
                pass  # If we can't check size, proceed with append

        # Atomic append: write entire line in single write() call
        with open(coverage_path, "a") as f:
            f.write(json.dumps(entry.__dict__) + "\n")
        return True
    except OSError:
        return False


def _read_skill_usage_log(project_root: Path) -> list[SkillCoverageEntry]:
    """Read skill usage log from project's .evidence directory.

    This is the log written by state_manager.log_skill_run() in run_gto_monorepo.py.
    Kept separate from the home-based skill_coverage log for historical reasons.

    Args:
        project_root: Project root directory

    Returns:
        List of SkillCoverageEntry objects
    """
    usage_path = project_root / ".evidence" / "skill-usage.jsonl"
    if not usage_path.exists():
        return []

    entries = []
    try:
        with open(usage_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    entries.append(
                        SkillCoverageEntry(
                            skill=data.get("skill", ""),
                            target=data.get("target", ""),
                            terminal_id=data.get("terminal_id", ""),
                            timestamp=data.get("timestamp", ""),
                            git_sha=data.get("git_sha"),
                            gap_ids_targeted=data.get("gap_ids_targeted", []),
                        )
                    )
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass

    return entries


def _had_recent_git_activity(project_root: Path, hours: int = 48) -> tuple[bool, str | None]:
    """Check if project had git commits in the last N hours.

    Handles monorepo subdirectories: if project_root is not a git repo,
    walks up to find the parent git repo and checks commits affecting
    the subdirectory path.

    Args:
        project_root: Project root directory
        hours: Number of hours to look back (default 48)

    Returns:
        Tuple of (had_activity, last_commit_sha or None)
    """
    # Try git in project_root first; if that fails, walk up to find the git repo
    cwd = project_root
    while True:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                break  # Found git repo
            # Not a git repo — try parent
            parent = cwd.parent
            if parent == cwd:
                return (False, None)  # Reached filesystem root
            cwd = parent
        except (subprocess.TimeoutExpired, OSError):
            return (False, None)

    # At this point cwd is the git repo root and project_root is the subdir
    try:
        # Check commits in the last N hours that affect the subdir path
        result = subprocess.run(
            ["git", "log", f"--since={hours} hours ago", "--pretty=format:%H", "--", str(project_root)],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            first_sha = result.stdout.strip().split("\n")[0]
            return (True, first_sha)
        return (False, None)
    except (subprocess.TimeoutExpired, OSError):
        return (False, None)


def _is_git_dirty_since(project_root: Path, target_key: str, timestamp: str) -> tuple[bool, bool]:
    """Check if files matching target_key changed since timestamp.

    Uses git log to check for commits after the timestamp that affect the target.

    Args:
        project_root: Project root directory
        target_key: Target key to check
        timestamp: ISO timestamp to check from

    Returns:
        Tuple of (is_stale, git_unavailable)
        - is_stale: True if target changed since timestamp
        - git_unavailable: True if git check failed (not installed, not repo, etc.)
    """
    try:
        # Check if there are commits after timestamp that affect the target
        result = subprocess.run(
            ["git", "log", "--since", timestamp, "--pretty=format:", "--name-only", "."],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            # Git error - could be not a repo, no git, etc.
            return (False, True)

        # Check if any changed files match the target key
        changed_files = result.stdout.strip().split("\n")
        for changed_file in changed_files:
            if not changed_file:
                continue
            # Simple prefix match - if target_key is "skills/usm" and file is "skills/usm/foo.py"
            if changed_file.startswith(target_key) or target_key in changed_file:
                return (True, False)

        return (False, False)
    except subprocess.TimeoutExpired:
        # Timeout - git was slow, treat as unavailable
        return (False, True)
    except OSError:
        # Git command not found or other OS error
        return (False, True)


def _classify_project_type(project_root: Path) -> list[SkillSuggestion]:
    """Classify project type and suggest relevant skills.

    Args:
        project_root: Project root directory

    Returns:
        List of SkillSuggestion objects based on project type
    """
    suggestions = []

    for project_type in PROJECT_TYPE_SKILLS:
        matched = False
        for pattern, _ in project_type["patterns"]:
            # Glob for files matching the pattern
            matches = list(project_root.glob(pattern))
            if matches:
                matched = True
                break

        if not matched:
            continue

        # Check negative patterns (must NOT exist)
        negative_match = False
        for neg_pattern, must_exist_dir in project_type["negative_patterns"]:
            neg_matches = list(project_root.glob(neg_pattern))
            if must_exist_dir:
                # Directory must exist for this to be a negative match
                if neg_matches:
                    negative_match = True
                    break
            else:
                # Any match is a negative
                if neg_matches:
                    negative_match = True
                    break

        if negative_match:
            continue

        # This project type matched
        suggestions.append(
            SkillSuggestion(
                skill=project_type["suggestion"],
                reason=project_type["reason"],
                priority="LOW",
            )
        )

    return suggestions


def detect_skill_coverage(
    project_root: Path | str | None = None,
    target_key: str = "",
    gaps: list[dict] | None = None,
) -> list[dict]:
    """Detect skill coverage and return suggestions as RSN findings.

    This is the main entry point for the skill coverage detector.
    It:
    1. If gaps provided: Uses gap-aware skill recommendations
    2. If no gaps: Falls back to project type heuristics
    3. Reads skill coverage log for freshness tracking
    4. Returns skill suggestions as RSN-format findings

    Args:
        project_root: Project root directory (defaults to cwd)
        target_key: Target key (path relative to project_root)
        gaps: Optional list of gap findings from GTO analysis.
              When provided, recommendations are gap-aware.

    Returns:
        List of RSN-format finding dicts with action_type="Use /skill"
    """
    project_root = Path(project_root or Path.cwd()).resolve()
    findings = []

    # Step 0: Read coverage log BEFORE recommendations so we can mark verified skills
    coverage_path = _get_skill_coverage_path(target_key)
    entries = _read_skill_coverage_log(coverage_path)
    project_entries = _read_skill_usage_log(project_root)
    all_entries = entries + project_entries

    # Determine which skills have FRESH coverage (ran with no file changes since)
    fresh_coverage_skills: set[str] = set()
    for entry in all_entries:
        if entry.timestamp:
            is_stale, git_unavailable = _is_git_dirty_since(
                project_root, target_key, entry.timestamp
            )
            # Only mark coverage as fresh if git was available AND no changes detected
            if not is_stale and not git_unavailable:
                fresh_coverage_skills.add(entry.skill)

    # Step 1: Gap-aware skill recommendations (if gaps provided)
    if gaps:
        logger.info("Using gap-aware skill recommendations for %d gaps", len(gaps))

        # Generate skill recommendations based on gaps
        recommendations = generate_skill_recommendations(gaps, limit=5)

        # Collect gap types for effectiveness scoring
        gap_types = list({g.get("type", "") for g in gaps if g.get("type")})

        # Apply resolution-effectiveness weighting to each recommendation
        for rec in recommendations:
            score = get_skill_effectiveness_score(target_key, rec.skill.name, gap_types)
            # Boost confidence if skill historically resolved these gap types
            if score > 0.7:
                rec.confidence = min(rec.confidence + 0.15, 0.95)
            # Demote if skill has poor track record on these gap types
            elif score < 0.3:
                rec.confidence = max(rec.confidence - 0.1, 0.1)
            # Mark verified if skill has fresh coverage evidence
            if rec.skill.name in fresh_coverage_skills:
                rec.verified = True

        # Convert to RSN findings
        gap_aware_findings = format_recommendations_for_rsn(recommendations)
        findings.extend(gap_aware_findings)

        # Add skill context for LLM (injects into RSN output)
        skill_context = inject_skill_context_for_gaps(gaps)
        if skill_context and findings:
            # Add context as metadata to first finding
            findings[0]["skill_context"] = skill_context

    # Step 2.5: Also read skills from package CHANGELOG.md (shared skill activity log)
    # This supplements the JSONL logs — skills that write to CHANGELOG.md are tracked here
    changelog_skills: set[str] = set()
    if _get_changelog_skills is not None:
        try:
            changelog_skills = _get_changelog_skills(project_root / "CHANGELOG.md")
        except Exception:
            changelog_skills = set()
        logger.info("Changelog skills read: %s", changelog_skills)

    # Step 3: Track which skills have already been run (and coverage is fresh)
    skills_run: set[str] = set()
    now = datetime.now().isoformat()

    # Include skills from package CHANGELOG.md
    skills_run.update(changelog_skills)

    for entry in all_entries:
        skills_run.add(entry.skill)

        # Check freshness - if file changed since last run, mark as stale
        if entry.timestamp:
            is_stale, git_unavailable = _is_git_dirty_since(
                project_root, target_key, entry.timestamp
            )
            if is_stale:
                # Add a note that coverage may be stale
                findings.append(
                    {
                        "id": f"SKILL-STALE-{entry.skill.replace('/', '-')}",
                        "severity": "LOW",
                        "message": f"{entry.skill} was run on this target but files have changed since",
                        "action_type": "Use /skill",
                        "domain": "skill_suggestion",
                        "effort_estimate_minutes": 5,
                        "gap_id": f"SKILL-STALE-{entry.skill.replace('/', '-')}",
                        "type": "skill_suggestion",
                        "file_ref": None,
                    }
                )
            elif git_unavailable:
                # Git check failed - surface a warning finding
                findings.append(
                    {
                        "id": f"SKILL-GIT-WARN-{entry.skill.replace('/', '-')}",
                        "severity": "LOW",
                        "message": f"{entry.skill} was recorded but git status check failed - coverage freshness unknown",
                        "action_type": "Use /skill",
                        "domain": "skill_suggestion",
                        "effort_estimate_minutes": 5,
                        "gap_id": f"SKILL-GIT-WARN-{entry.skill.replace('/', '-')}",
                        "type": "skill_suggestion",
                        "file_ref": None,
                    }
                )

    # ── Dedup: filter out skill suggestions for already-run skills ──────────────
    # skills_run is now complete (changelog + JSONL). Filter any gap-aware or
    # project-type skill suggestions that match already-run skills.
    if skills_run:
        logger.info("Skills already run on this target: %s", skills_run)
        _SKILL_ACTION_TYPES = frozenset(("Use /skill", "Run skill"))

        def _is_duplicate_skill(f: dict, skills: set[str]) -> bool:
            """Return True if f is a skill suggestion for a skill already in skills."""
            if f.get("action_type") not in _SKILL_ACTION_TYPES:
                return False
            msg = f.get("message", "")
            for skill in skills:
                if msg.startswith(f"Run {skill} ") or msg.startswith(f"{skill} "):
                    return True
            return False

        findings = [f for f in findings if not _is_duplicate_skill(f, skills_run)]

    # Step 4: Fallback to project type heuristics (if no gaps or as supplement)
    if not gaps:
        logger.info("No gaps provided, using project type heuristics")
        project_suggestions = _classify_project_type(project_root)

        for suggestion in project_suggestions:
            # Skip if this skill was already run with fresh coverage
            if suggestion.skill in skills_run:
                # Check git freshness - if no entries, use current time
                # Use MOST RECENT entry (entries[-1] after sorting) for freshness check
                check_timestamp = entries[-1].timestamp if entries else now
                is_stale, git_unavailable = _is_git_dirty_since(
                    project_root, target_key, check_timestamp
                )
                if not is_stale and not git_unavailable:
                    # Fresh coverage exists, skip this suggestion
                    continue

            findings.append(
                {
                    "id": f"SKILL-SUGGEST-{suggestion.skill.replace('/', '-')}",
                    "severity": suggestion.priority,
                    "message": f"{suggestion.reason} — try {suggestion.skill}",
                    "action_type": "Use /skill",
                    "domain": "skill_suggestion",
                    "effort_estimate_minutes": 5,
                    "gap_id": f"SKILL-SUGGEST-{suggestion.skill.replace('/', '-')}",
                    "type": "skill_suggestion",
                    "file_ref": None,
                }
            )

    # Step 5: Verification skills for skills/hooks projects — suggest /verify and /pre-mortem
    # when they haven't been run on this target. These catch gaps that other
    # detectors miss (e.g. after a rename, structural refactor, or major change
    # that didn't surface as a specific gap type).
    if not gaps:
        verify_skills = {"/verify", "/pre-mortem"}
        for skill in verify_skills:
            if skill not in skills_run:
                findings.append(
                    {
                        "id": f"SKILL-CHANGE-{skill.replace('/', '-')}",
                        "severity": "HIGH",
                        "message": (
                            f"{skill} recommended — no evidence of this verification "
                            "skill having been run on this target. Run to surface gaps."
                        ),
                        "action_type": "Use /skill",
                        "domain": "skill_suggestion",
                        "effort_estimate_minutes": 10,
                        "gap_id": f"SKILL-CHANGE-{skill.replace('/', '-')}",
                        "type": "skill_suggestion",
                        "file_ref": None,
                    }
                )

    return findings


# Convenience function
def get_skill_coverage_suggestions(
    project_root: Path | str | None = None,
    target_key: str = "",
) -> SkillCoverageResult:
    """Get skill coverage result with metadata.

    Args:
        project_root: Project root directory
        target_key: Target key (path relative to project_root)

    Returns:
        SkillCoverageResult with suggestions and metadata
    """
    project_root = Path(project_root or Path.cwd()).resolve()
    coverage_path = _get_skill_coverage_path(target_key)
    entries = _read_skill_coverage_log(coverage_path)

    suggestions = []
    skills_already_run = []

    for entry in entries:
        skills_already_run.append(entry.skill)

    # Get project type suggestions
    project_suggestions = _classify_project_type(project_root)

    for suggestion in project_suggestions:
        if suggestion.skill not in skills_already_run:
            suggestions.append(suggestion)

    return SkillCoverageResult(
        suggestions=suggestions,
        coverage_log_exists=coverage_path.exists(),
        skills_already_run=skills_already_run,
        target_key=target_key,
    )
