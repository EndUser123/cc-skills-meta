#!/usr/bin/env python3
"""
/learn - Intelligent Lesson Capture

Adaptive lesson extraction that figures out what you actually learned.
Uses novelty detection (CKS queries) and usefulness scoring.

Enhanced with LangMem-inspired episodic memory structure:
- Episode schema: observation → thoughts → action → result
- Captures context for "what worked/didn't" sections

This skill is self-contained and uses local modules in the skill directory.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Self-contained: use local modules in skill directory
_SKILL_DIR = Path(__file__).parent.resolve()
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from retrospective_common import (
    extract_and_store,
    find_chs_references,
    get_session_context,
    store_direct_lessons,
    store_to_cks,
)


def parse_triage_lesson(text: str) -> dict[str, str | int] | None:
    """Parse triage correction lesson in format: "FINDING_ID CORRECTED - ORIGINAL - context".

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
        # High confidence indicators (explicit user corrections)
        if any(keyword in context_lower for keyword in ["user", "corrected", "explicit", "review"]):
            score = 7
        # Medium confidence indicators (pattern observations)
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
    """Parse lesson text in format: "Lesson text - Category (severity)".

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


def get_transcript_path(cli_args: list[str]) -> str | None:
    """Discover transcript path from environment, cwd, or CLI argument."""
    # Check environment variable first
    import os

    transcript_path = os.environ.get("CLAUDE_TRANSCRIPT_PATH")

    # Auto-discover: find most recent .jsonl in cwd or default location
    if not transcript_path:
        # Try cwd first (portable)
        project_dir = Path.cwd()
        jsonl_files = list(project_dir.glob("*.jsonl"))

        # Fallback to Claude Code projects directory (relative to home)
        if not jsonl_files:
            home_projects = Path.home() / ".claude" / "projects"
            if home_projects.exists():
                # Try to find a project directory with jsonl files
                for project in home_projects.iterdir():
                    if project.is_dir():
                        jsonl_files = list(project.glob("*.jsonl"))
                        if jsonl_files:
                            break

        if jsonl_files:
            # Sort by modification time, get most recent
            transcript_path = str(max(jsonl_files, key=lambda p: p.stat().st_mtime))

    # Check CLI arguments for explicit path
    if not transcript_path:
        for arg in cli_args:
            if arg.endswith(".jsonl") and Path(arg).exists():
                transcript_path = str(Path(arg).resolve())
                break

    return transcript_path


def print_usage():
    """Print usage information."""
    print("""
/learn - Intelligent Lesson Capture

USAGE:
    /learn [options]                          # Extract from transcript
    /learn --lesson "Lesson text - Category"  # Store single lesson
    /learn --stdin                            # Store multiple lessons from stdin

LESSON FORMAT:
    "Lesson text - Category (severity)"

    Examples:
    /learn --lesson "Exit code 0 with JSON is official Claude Code hook pattern - technical (critical)"
    /learn --lesson "Tavily MCP outperforms regular web searches - tooling (important)"

    cat lessons.txt | /learn --stdin

    Severity levels: critical (8), important (6), nice-to-know (4)
    Only lessons with score ≥ 4 are stored.

OPTIONS:
    --verbose, -v      Show detailed output
    --dry-run, -n      Parse but don't store
    --help, -h         Show this help message
    """)


def main() -> int:
    """Main entry point for /learn skill."""
    # Parse arguments
    cli_args = sys.argv[1:]  # Exclude script name
    verbose = "--verbose" in cli_args or "-v" in cli_args
    dry_run = "--dry-run" in cli_args or "-n" in cli_args

    # Check for help
    if "--help" in cli_args or "-h" in cli_args:
        print_usage()
        return 0

    # Check for direct lesson storage mode
    # Accepts: --lesson "text", or bare positional args: "Lesson text - category"
    lesson_texts = []
    if "--lesson" in cli_args:
        lesson_idx = cli_args.index("--lesson")
        if lesson_idx + 1 >= len(cli_args):
            print("❌ --lesson requires an argument")
            print('   Usage: /learn --lesson "Lesson text - Category (severity)"')
            return 1
        lesson_texts.append(cli_args[lesson_idx + 1])
    else:
        # Bare positional args: treat each as a lesson text
        for arg in cli_args:
            if arg.startswith("-"):
                continue  # skip flags
            lesson_texts.append(arg)

    if lesson_texts:
        stored_ids = store_direct_lessons(lesson_texts, dry_run=dry_run, verbose=verbose)

        if verbose and stored_ids:
            print(f"\n✓ Stored {len(stored_ids)} lesson(s)")
        elif verbose:
            print("\nNo lessons stored")

        return 0

    # Check for stdin mode
    if "--stdin" in cli_args:
        # Read lessons from stdin
        lesson_texts = []
        try:
            for line in sys.stdin:
                line = line.strip()
                if line:
                    lesson_texts.append(line)
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted")
            return 1

        if not lesson_texts:
            print("❌ No lessons provided via stdin")
            return 1

        stored_ids = store_direct_lessons(lesson_texts, dry_run=dry_run, verbose=True)

        if verbose and stored_ids:
            print(f"\n✓ Stored {len(stored_ids)} lesson(s)")
        elif verbose:
            print("\nNo lessons stored")

        return 0

    # Default: transcript extraction mode
    transcript_path = get_transcript_path(cli_args)

    if not transcript_path:
        print(
            "❌ No transcript found. Run from a project directory with .jsonl files, or specify path:"
        )
        print("   /learn path/to/transcript.jsonl")
        print("\nOr use direct lesson storage:")
        print('   /learn --lesson "Lesson text - Category (severity)"')
        print("   cat lessons.txt | /learn --stdin")
        return 1

    # Run extraction (show_output=True for interactive use)
    result = extract_and_store(
        transcript_path=transcript_path,
        verbose=verbose,
        dry_run=dry_run,
        show_output=True,
        threshold=4,
    )

    # Exit code based on whether anything was stored
    if dry_run:
        return 0  # Dry run always succeeds
    elif result.stored_ids:
        return 0  # Success - lessons stored
    elif result.lessons:
        return 0  # Still success - lessons found but below threshold
    else:
        return 0  # No lessons is not an error


if __name__ == "__main__":
    sys.exit(main())
