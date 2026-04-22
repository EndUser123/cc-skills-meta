#!/usr/bin/env python
"""
Historical Transcript Scanning Module

Scans ~/.claude/session-env/*.jsonl files to extract signals from
past sessions and add them to the learning queue.

Features:
- Discovers all session transcript files
- Extracts user corrections, approvals, and tool errors
- Calculates confidence scores from context
- Adds only new fingerprints to queue (no duplicates)
- Handles malformed transcripts gracefully
"""

import json
import re
from pathlib import Path
from typing import Any

from learning_ledger import LearningLedger

# Correction patterns from capture_learnings.py
CORRECTION_PATTERNS = [
    r"^no,\s+(.+?)(?:\s+instead)?$",
    r"^not\s+(.+?)(?:\s+instead)?$",
    r"^wrong(?:,\s*(.+))?$",
    r"^incorrect(?:,\s*(.+))?$",
    r"^don't\s+(?:use|do)(?:,\s*(.+))?$",
    r"^stop(?:,\s*(.+))?$",
    r"^(.+?)\s+is\s+(?:wrong|incorrect)$",
]

APPROVAL_PATTERNS = [
    r"^yes(?:,\s*(.+))?$",
    r"^correct(?:,\s*(.+))?$",
    r"^good(?:,\s*(.+))?$",
    r"^right(?:,\s*(.+))?$",
    r"^perfect(?:,\s*(.+))?$",
    r"^great(?:,\s*(.+))?$",
    r"^exactly(?:,\s*(.+))?$",
    r"^that's\s+(?:correct|right|good)(?:,\s*(.+))?$",
]


def scan_sessions(limit: int = None) -> dict[str, Any]:
    """
    Scan all session transcripts and extract signals.

    Args:
        limit: Maximum number of session files to scan (None = all).

    Returns:
        Summary dict with:
            - scanned: Number of session files scanned
            - signals_found: Total signals extracted
            - added: Number of new learnings added to queue
            - skipped: Number of duplicates skipped
            - errors: Number of errors encountered
    """
    session_env_path = Path.home() / ".claude" / "session-env"

    if not session_env_path.exists():
        return {
            "scanned": 0,
            "signals_found": 0,
            "added": 0,
            "skipped": 0,
            "errors": 0,
            "message": "session-env directory not found",
        }

    # Discover all .jsonl files
    jsonl_files = list(session_env_path.glob("*.jsonl"))

    if not jsonl_files:
        return {
            "scanned": 0,
            "signals_found": 0,
            "added": 0,
            "skipped": 0,
            "errors": 0,
            "message": "No session files found",
        }

    # Apply limit if specified
    if limit:
        jsonl_files = jsonl_files[:limit]

    ledger = LearningLedger()

    summary = {
        "scanned": 0,
        "signals_found": 0,
        "added": 0,
        "skipped": 0,
        "errors": 0,
    }

    # Scan each session file
    for session_file in jsonl_files:
        try:
            signals = _scan_session_file(session_file)
            summary["scanned"] += 1
            summary["signals_found"] += len(signals)

            # Add signals to ledger
            for signal in signals:
                result = ledger.record_learning(
                    content=signal["content"],
                    learning_type=signal["type"],
                    skill_name=signal.get("skill_name", "unknown"),
                    confidence=signal["confidence"],
                )

                if result["action"] == "created":
                    summary["added"] += 1
                elif result["action"] == "exists":
                    summary["skipped"] += 1

        except Exception:
            summary["errors"] += 1
            # Continue scanning other files

    return summary


def _scan_session_file(session_path: Path) -> list[dict[str, Any]]:
    """
    Scan a single session file for signals.

    Args:
        session_path: Path to the .jsonl session file.

    Returns:
        List of signal dicts extracted from the transcript.
    """
    signals = []

    try:
        with open(session_path, encoding="utf-8") as f:
            transcript = []
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                    transcript.append(entry)
                except json.JSONDecodeError:
                    # Skip malformed JSON lines
                    continue

        # Extract signals from transcript
        signals = extract_signals_from_transcript(transcript)

    except Exception:
        # Return empty list on file read errors
        pass

    return signals


def extract_signals_from_transcript(transcript: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Extract learning signals from a transcript.

    Args:
        transcript: List of transcript entries (dicts with 'role' and 'content').

    Returns:
        List of signal dicts with keys: content, type, confidence, skill_name.
    """
    signals = []
    i = 0

    while i < len(transcript):
        entry = transcript[i]

        # Only process user messages
        if entry.get("role") != "user":
            i += 1
            continue

        content = entry.get("content", "")
        if not content:
            i += 1
            continue

        # Check for correction patterns
        correction = _detect_correction(content)
        if correction:
            confidence = _calculate_confidence(content, "correction")
            signals.append(
                {
                    "content": correction,
                    "type": "correction",
                    "confidence": confidence,
                    "skill_name": _extract_skill_name(transcript, i),
                }
            )
            i += 1
            continue

        # Check for approval patterns
        approval = _detect_approval(content)
        if approval:
            confidence = _calculate_confidence(content, "approval")
            signals.append(
                {
                    "content": approval,
                    "type": "approval",
                    "confidence": confidence,
                    "skill_name": _extract_skill_name(transcript, i),
                }
            )
            i += 1
            continue

        # Check for tool error patterns
        tool_error = _detect_tool_error(transcript, i)
        if tool_error:
            confidence = _calculate_confidence(content, "correction")
            signals.append(
                {
                    "content": tool_error,
                    "type": "tool_error",
                    "confidence": confidence,
                    "skill_name": _extract_skill_name(transcript, i),
                }
            )
            i += 1
            continue

        i += 1

    return signals


def _detect_correction(content: str) -> str:
    """Detect if content is a correction and extract the corrected message."""
    content_lower = content.lower().strip()

    for pattern in CORRECTION_PATTERNS:
        match = re.match(pattern, content_lower)
        if match:
            # Return the full original content as the correction
            return content

    return None


def _detect_approval(content: str) -> str:
    """Detect if content is an approval and extract the approved message."""
    content_lower = content.lower().strip()

    for pattern in APPROVAL_PATTERNS:
        match = re.match(pattern, content_lower)
        if match:
            return content

    return None


def _detect_tool_error(transcript: list[dict[str, Any]], idx: int) -> str:
    """
    Detect tool error followed by user correction.

    Pattern: Assistant calls tool → Tool returns error → User provides fix
    """
    # Check if previous entry was a tool error
    if idx > 0 and transcript[idx - 1].get("role") == "tool":
        tool_content = transcript[idx - 1].get("content", "")

        # Check if tool content contains error
        if "error" in tool_content.lower() or "failed" in tool_content.lower():
            # User is responding to a tool error
            return transcript[idx].get("content", "")

    return None


def _calculate_confidence(content: str, signal_type: str) -> float:
    """
    Calculate confidence score based on content and type.

    Rules:
    - Strong corrections ("WRONG!", "STOP!") → 0.95
    - Normal corrections → 0.85
    - Approvals → 0.75
    - Weak signals ("maybe", "could we") → 0.65
    """
    content_upper = content.upper()
    signal_type_lower = signal_type.lower()

    # Strong indicators
    if any(word in content_upper for word in ["WRONG!", "STOP!", "NO!", "DON'T"]):
        return 0.95

    # Normal corrections
    if signal_type_lower == "correction":
        return 0.85

    # Approvals
    if signal_type_lower == "approval":
        return 0.75

    # Tool errors
    if signal_type_lower == "tool_error":
        return 0.80

    # Weak signals
    if any(word in content_upper for word in ["MAYBE", "COULD WE", "WHAT IF"]):
        return 0.65

    # Default
    return 0.70


def _extract_skill_name(transcript: list[dict[str, Any]], idx: int) -> str:
    """
    Extract skill name from transcript context.

    Look for skill invocation patterns in previous messages.
    """
    # Look backward for skill invocation
    for i in range(max(0, idx - 5), idx):
        entry = transcript[i]
        content = entry.get("content", "")

        # Look for /skill-name or [skill-name] patterns
        skill_match = re.search(r"[\/\[](\w+)[\]:\s]", content)
        if skill_match:
            return skill_match.group(1)

    return "unknown"


if __name__ == "__main__":
    # Test mode: scan last 5 sessions
    import sys

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    print(f"Scanning last {limit} sessions...\n")
    summary = scan_sessions(limit=limit)

    print(f"Sessions scanned: {summary['scanned']}")
    print(f"Signals found: {summary['signals_found']}")
    print(f"Added to queue: {summary['added']}")
    print(f"Skipped (duplicates): {summary['skipped']}")
    print(f"Errors: {summary['errors']}")

    if "message" in summary:
        print(f"\n{summary['message']}")
