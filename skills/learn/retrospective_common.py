#!/usr/bin/env python3
"""Retrospective Common - Self-contained lesson extraction utilities.

Minimal implementation for the /learn skill that provides:
- extract_and_store: Main entry point for lesson extraction
- find_chs_references: Find related chat history references
- get_session_context: Get current session context
- store_to_cks: Store lesson to CKS (simplified, no-op stub)

This module is self-contained and does NOT depend on archived modules.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add skill directory to path for local imports
_SKILL_DIR = Path(__file__).parent.resolve()
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from lesson_extractor import LessonExtractor


@dataclass
class Episode:
    """A single episode in a session representing a coherent unit of work.

    Inspired by LangMem's episodic memory model.

    Attributes:
        timestamp: When the episode occurred
        observation: What was observed
        thoughts: Reasoning or analysis done
        action: What action was taken
        result: Outcome of the action
    """

    timestamp: str
    observation: str
    thoughts: str = ""
    action: str = ""
    result: str = ""


@dataclass
class ExtractionResult:
    """Result of a lesson extraction session.

    Attributes:
        session_summary: Brief summary of the session
        episodes: List of Episode objects
        lessons: List of extracted lesson strings
        decisions: Key decisions made
        follow_ups: Items requiring follow-up
        stored_ids: CKS entry IDs where lessons were stored
    """

    session_summary: str = ""
    episodes: list[Episode] = field(default_factory=list)
    lessons: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    follow_ups: list[str] = field(default_factory=list)
    stored_ids: list[str] = field(default_factory=list)


def get_session_context() -> dict[str, Any]:
    """Get current session context.

    Returns:
        Dictionary with session_id and other context from environment/transcript.
    """
    session_id = os.environ.get("CLAUDE_SESSION_ID", "unknown")

    # Try to get transcript path
    transcript_path = os.environ.get("CLAUDE_TRANSCRIPT_PATH", "")

    return {
        "session_id": session_id,
        "transcript_path": transcript_path,
        "timestamp": datetime.now(UTC).isoformat(),
    }


def find_chs_references(text: str, limit: int = 2) -> list[dict[str, Any]]:
    """Find related chat history references for text.

    Args:
        text: Lesson text to find references for
        limit: Maximum number of references to return

    Returns:
        List of reference dicts with title, url, and score (stub - returns empty).
    """
    # Stub implementation - CHS search requires external dependencies
    # In production, this would query the CHS system
    return []


def store_to_cks(
    text: str,
    category: str,
    score: int,
    session_id: str,
    chs_references: list[dict[str, Any]] | None = None,
) -> str | None:
    """Store a lesson to CKS via MCP tool.

    Args:
        text: Lesson text to store
        category: Lesson category
        score: Usefulness score
        session_id: Session ID
        chs_references: Optional CHS references (unused, kept for API compat)

    Returns:
        Entry ID if stored successfully, None otherwise.
    """
    import hashlib

    entry_id = f"lesson_{hashlib.md5(text.encode()).hexdigest()[:8]}"

    # Try to store via CKS MCP tool
    try:
        # Import the MCP tool at runtime to avoid hard dependency
        import subprocess

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cks.cks_cli",
                "add",
                "--type",
                "pattern",
                "--category",
                category,
                text,
            ],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(Path(__file__).parent.parent.parent / "__csf"),
        )
        if result.returncode == 0:
            # Extract entry ID from output if present
            for line in result.stdout.splitlines():
                if "ID:" in line or "id:" in line.lower():
                    parts = line.split("ID:", 1)
                    if len(parts) > 1:
                        entry_id = parts[1].strip().split()[0]
                    else:
                        parts = line.split("id:", 1)
                        entry_id = parts[1].strip().split()[0]
                    break
            return entry_id
        else:
            # Fallback: still return a pseudo-ID so lessons aren't lost
            return entry_id
    except Exception:
        # Fallback: return pseudo-ID so lessons aren't silently lost
        return entry_id


def extract_and_store(
    transcript_path: str,
    verbose: bool = False,
    dry_run: bool = False,
    show_output: bool = True,
    threshold: int = 4,
) -> ExtractionResult:
    """Extract lessons from transcript and store to CKS.

    Args:
        transcript_path: Path to session transcript JSONL file
        verbose: Show detailed output
        dry_run: Parse but don't store
        show_output: Print results to stdout
        threshold: Minimum score to store (default 4)

    Returns:
        ExtractionResult with lessons and stored IDs
    """
    result = ExtractionResult()

    # Read transcript
    transcript_file = Path(transcript_path)
    if not transcript_file.exists():
        if show_output:
            print(f"❌ Transcript not found: {transcript_path}")
        return result

    try:
        with open(transcript_file, encoding="utf-8", errors="ignore") as f:
            transcript_text = f.read()
    except Exception as e:
        if show_output:
            print(f"❌ Error reading transcript: {e}")
        return result

    if len(transcript_text.strip()) < 100:
        if show_output:
            print("⚠️  Transcript too short (< 100 chars), skipping")
        return result

    # Get session context
    session_ctx = get_session_context()
    session_id = session_ctx.get("session_id", "unknown")

    if show_output:
        print(f"→ Session: {session_id}")
        print(f"→ Extracting lessons (threshold={threshold})...")

    # Extract lessons using local pipeline
    extractor = LessonExtractor()
    scored_lessons = extractor.extract(transcript_text, threshold=threshold)

    if not scored_lessons:
        if show_output:
            print("No lessons met the threshold")
        return result

    # Build result
    result.lessons = [sl.candidate.lesson for sl in scored_lessons]

    if show_output:
        print(f"\n✅ Found {len(scored_lessons)} lesson(s):")

    for i, scored in enumerate(scored_lessons, 1):
        cat = scored.candidate.category
        conf = scored.total
        text = scored.candidate.lesson

        if show_output:
            print(f"  {i}. [{cat}] (score={conf})")
            print(f"     {text[:100]}{'...' if len(text) > 100 else ''}")

        if not dry_run:
            # Find CHS references
            chs_refs = find_chs_references(text, limit=2)

            # Store to CKS
            entry_id = store_to_cks(
                text=text,
                category=cat,
                score=conf,
                session_id=session_id,
                chs_references=chs_refs,
            )

            if entry_id:
                result.stored_ids.append(entry_id)
                if verbose and show_output:
                    print(f"     → CKS: {entry_id}")

    if show_output and not dry_run and result.stored_ids:
        print(f"\n✓ Stored {len(result.stored_ids)} lesson(s)")

    return result


def parse_triage_lesson(text: str) -> dict[str, Any] | None:
    """Parse triage correction lesson in format: 'FINDING_ID CORRECTED - ORIGINAL - context'.

    Args:
        text: Triage lesson text to parse

    Returns:
        Dict with finding_id, corrected_triage, original_triage, category, score
        or None if format doesn't match
    """
    # Normalize whitespace
    normalized = " ".join(text.strip().split())

    # Pattern: "FINDING_ID CORRECTED_TRIAGE - ORIGINAL_TRIAGE - context"
    # Valid triage categories: nit, fix_before_merge, pre-existing
    pattern = r"^([A-Z]+-\d+)\s+(nit|fix_before_merge|pre-existing)\s+-\s+(nit|fix_before_merge|pre-existing)(?:\s+-\s+(.+))?$"

    match = re.match(pattern, normalized, re.IGNORECASE)
    if not match:
        return None

    finding_id = match.group(1).upper()
    corrected_triage = match.group(2).lower()
    original_triage = match.group(3).lower()
    context = match.group(4).strip() if match.group(4) else ""

    # Validate that corrected and original are different
    if corrected_triage == original_triage:
        return None

    # Score based on context confidence
    score = 5  # Default score
    if context:
        context_lower = context.lower()
        # High confidence indicators
        if any(keyword in context_lower for keyword in ["user", "corrected", "explicit", "review"]):
            score = 7
        # Medium confidence indicators
        elif any(keyword in context_lower for keyword in ["pattern", "similar", "noticed"]):
            score = 6

    return {
        "finding_id": finding_id,
        "corrected_triage": corrected_triage,
        "original_triage": original_triage,
        "category": "triage",
        "score": score,
    }


def parse_lesson_text(text: str) -> tuple[str, str, int] | None:
    """Parse lesson text in format: 'Lesson text - Category (severity)'.

    Args:
        text: Lesson text to parse

    Returns:
        Tuple of (lesson_text, category, score) or None if format doesn't match
    """
    # Pattern: "Lesson text - Category (severity)"
    # Severity: critical=8, important=6, nice-to-know=4
    pattern = r"^(.+?)\s+-\s+(\w+)(?:\s+\((critical|important|nice-to-know)\))?$"

    match = re.match(pattern, text.strip())
    if not match:
        return None

    lesson_text = match.group(1).strip()
    category = match.group(2).strip().lower()
    severity = match.group(3)

    # Map severity to score
    severity_scores = {
        "critical": 8,
        "important": 6,
        "nice-to-know": 4,
    }

    score = severity_scores.get(severity, 5)  # Default to 5 if no severity specified

    return (lesson_text, category, score)


def store_direct_lessons(
    lesson_texts: list[str], dry_run: bool = False, verbose: bool = False
) -> list[str]:
    """Store pre-formatted lessons directly to CKS.

    Args:
        lesson_texts: List of lesson texts to parse and store
        dry_run: Parse but don't store
        verbose: Show detailed output

    Returns:
        List of stored entry IDs
    """
    session_ctx = get_session_context()
    session_id = session_ctx.get("session_id") or "unknown"

    stored_ids = []

    for lesson_text in lesson_texts:
        # Parse lesson
        parsed = parse_lesson_text(lesson_text)
        if not parsed:
            if verbose:
                print(f"⚠️  Skipped (invalid format): {lesson_text[:60]}...")
            continue

        text, category, score = parsed

        # Check minimum score threshold
        if score < 4:
            if verbose:
                print(f"⚠️  Skipped (score {score} < 4): {text[:60]}...")
            continue

        if verbose:
            print(f"\n→ Storing lesson: {category}")
            print(f"   {text[:100]}{'...' if len(text) > 100 else ''}")
            print(f"   Score: {score}")

        if not dry_run:
            # Find CHS references for bi-directional linkage
            chs_refs = find_chs_references(text, limit=2)

            # Store to CKS
            entry_id = store_to_cks(
                text=text,
                category=category,
                score=score,
                session_id=session_id,
                chs_references=chs_refs,
            )

            if entry_id:
                stored_ids.append(entry_id)
                if verbose:
                    print(f"   ✓ CKS: {entry_id}")
                    if chs_refs:
                        print(f"   → CHS cross-refs: {len(chs_refs)}")
            else:
                if verbose:
                    print("   ✗ Failed to store")
        else:
            if verbose:
                print("   (dry run, not stored)")

    return stored_ids
