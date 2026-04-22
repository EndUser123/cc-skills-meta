#!/usr/bin/env python
"""
Show Queue Module - Display pending learnings in review table.

This module queries the LearningLedger for pending learnings and formats
them into a readable table sorted by confidence score (descending).

Functions:
    format_queue_table: Format pending learnings as a review table.
    get_queue_summary: Get summary statistics for the queue.
"""

import sqlite3
from pathlib import Path
from typing import Any

import scope_analyzer
from learning_ledger import LearningLedger

# Column configuration for table display
_COLUMN_WIDTHS = {
    "ID": 10,
    "Content": 50,
    "Confidence": 12,
    "Scope": 10,
    "Targets": 35,
    "Status": 10,
}

# Default limit for number of learnings to display
_DEFAULT_LIMIT = 20


def format_queue_table(limit: int = _DEFAULT_LIMIT) -> str:
    """
    Format pending learnings as a review table.

    The table displays learnings sorted by confidence score (descending)
    with columns: ID, Content, Confidence, Skill, and Status.

    Args:
        limit: Maximum number of learnings to display (default: 20).

    Returns:
        Formatted table string with pending learnings, or a message
        indicating no pending learnings or an error.
    """
    ledger = LearningLedger()
    stats = ledger.get_stats()
    pending_count = stats.get("by_status", {}).get("pending", 0)

    if pending_count == 0:
        return "No pending learnings in queue."

    rows = _query_pending_learnings(ledger.db_path, limit)

    if not rows:
        return "No pending learnings in queue."

    return _format_table(rows)


def _query_pending_learnings(db_path: "str | Path", limit: int) -> list[sqlite3.Row]:
    """
    Query pending learnings from the database.

    Note: The 'scope' column doesn't exist yet (added in T-012),
    so we use 'skill_name' instead.

    Args:
        db_path: Path to the SQLite database.
        limit: Maximum number of records to return.

    Returns:
        List of database rows containing pending learnings.
    """
    query = """
        SELECT fingerprint, content, learning_type, confidence,
               skill_name, status, created_at
        FROM learnings
        WHERE status = 'pending'
        ORDER BY confidence DESC
        LIMIT ?
    """

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, (limit,))
            return cursor.fetchall()
    except Exception:
        # Return empty list on error; caller will handle it
        return []


def _format_table(rows: list[sqlite3.Row]) -> str:
    """
    Format database rows as a readable table.

    Args:
        rows: List of SQLite Row objects containing learning data.

    Returns:
        Formatted table string with header, separator, data rows,
        and summary line.
    """
    header = _build_header()
    separator = "-" * len(header)

    table_lines = [header, separator]

    for row in rows:
        table_lines.append(_format_row(row))

    # Add summary line
    table_lines.append("")
    table_lines.append(f"Total: {len(rows)} pending learning(s)")

    return "\n".join(table_lines)


def _build_header() -> str:
    """
    Build the table header row.

    Returns:
        Formatted header string with column names.
    """
    return "  ".join(
        [
            "ID".ljust(_COLUMN_WIDTHS["ID"]),
            "Content".ljust(_COLUMN_WIDTHS["Content"]),
            "Confidence".ljust(_COLUMN_WIDTHS["Confidence"]),
            "Scope".ljust(_COLUMN_WIDTHS["Scope"]),
            "Targets".ljust(_COLUMN_WIDTHS["Targets"]),
            "Status".ljust(_COLUMN_WIDTHS["Status"]),
        ]
    )


# ANSI color codes for terminal output
_ANSI_RED = "\033[91m"
_ANSI_YELLOW = "\033[93m"
_ANSI_GREEN = "\033[92m"
_ANSI_RESET = "\033[0m"


def _format_confidence(confidence: float) -> str:
    """
    Format confidence value with color coding.

    Color scheme (T-016):
        - ≥0.85: Red (high confidence, needs attention)
        - ≥0.70: Yellow (medium confidence)
        - <0.70: Green (low confidence, safe)

    Args:
        confidence: Confidence value (0.0-1.0).

    Returns:
        Formatted confidence string with ANSI color codes.
    """
    # Color coding based on confidence level
    if confidence >= 0.85:
        # High confidence - red
        return f"{_ANSI_RED}{confidence:.0%}{_ANSI_RESET}"
    elif confidence >= 0.70:
        # Medium confidence - yellow
        return f"{_ANSI_YELLOW}{confidence:.0%}{_ANSI_RESET}"
    else:
        # Low confidence - green
        return f"{_ANSI_GREEN}{confidence:.0%}{_ANSI_RESET}"


def _format_row(row: sqlite3.Row) -> str:
    """
    Format a single database row as a table row.

    Args:
        row: SQLite Row object containing learning data.

    Returns:
        Formatted row string with truncated content and formatted fields.
    """
    # Truncate content to fit column width
    content = row["content"]
    if len(content) > _COLUMN_WIDTHS["Content"]:
        content = content[: _COLUMN_WIDTHS["Content"] - 3] + "..."

    # Format confidence as percentage with color coding
    confidence_value = row["confidence"]
    confidence = _format_confidence(confidence_value)

    # Get skill name
    skill = row["skill_name"] or "unknown"

    # Determine scope and targets
    try:
        scope_analysis = scope_analyzer.analyze_learning(row["content"], skill)
        recommended_scope = scope_analysis.get("recommended_scope", "skill")
        display_scope = "project" if recommended_scope == "skill" else recommended_scope

        # Determine targets based on scope
        if display_scope == "global":
            targets = "~/.claude/CLAUDE.md"
        else:
            targets = f"~/.claude/skills/{skill}/SKILL.md"
    except Exception:
        display_scope = "unknown"
        targets = "Unknown"

    # Format status
    status = row["status"] or "pending"

    return "  ".join(
        [
            str(row["fingerprint"][:8]).ljust(_COLUMN_WIDTHS["ID"]),
            content.ljust(_COLUMN_WIDTHS["Content"]),
            confidence.ljust(_COLUMN_WIDTHS["Confidence"]),
            display_scope.ljust(_COLUMN_WIDTHS["Scope"]),
            targets.ljust(_COLUMN_WIDTHS["Targets"]),
            status.ljust(_COLUMN_WIDTHS["Status"]),
        ]
    )


def get_queue_summary() -> dict[str, Any]:
    """
    Get summary statistics for the queue.

    Returns a dictionary containing:
        - count: Total number of pending learnings.
        - avg_confidence: Average confidence score (0.0 if none).
        - scopes: Dictionary of learning counts by scope.

    Note: The 'scope' column doesn't exist yet (added in T-012),
    so this function will query the 'scope' column but fall back
    gracefully if it doesn't exist.

    Returns:
        Dictionary with queue statistics.
    """
    ledger = LearningLedger()
    stats = ledger.get_stats()
    pending_count = stats.get("by_status", {}).get("pending", 0)

    if pending_count == 0:
        return {"count": 0, "avg_confidence": 0.0, "scopes": {}}

    result = _query_summary_stats(ledger.db_path)

    # Ensure count matches ledger stats
    result["count"] = pending_count
    return result


def _query_summary_stats(db_path: "str | Path") -> dict[str, Any]:
    """
    Query database for summary statistics.

    Args:
        db_path: Path to the SQLite database.

    Returns:
        Dictionary with avg_confidence and scopes. Falls back to
        zero values on error.
    """
    query = """
        SELECT confidence, scope
        FROM learnings
        WHERE status = 'pending'
    """

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        if not rows:
            return {"avg_confidence": 0.0, "scopes": {}}

        avg_confidence = sum(r[0] for r in rows) / len(rows)
        scopes = _count_by_scope(rows)

        return {"avg_confidence": avg_confidence, "scopes": scopes}
    except Exception:
        # Fallback if scope column doesn't exist or other error
        return {"avg_confidence": 0.0, "scopes": {}}


def _count_by_scope(rows: list[tuple]) -> dict[str, int]:
    """
    Count learnings grouped by scope.

    Args:
        rows: List of tuples containing (confidence, scope).

    Returns:
        Dictionary mapping scope names to counts.
    """
    scopes: dict[str, int] = {}

    for row in rows:
        # row[1] is scope, which may be NULL
        scope = row[1] if row[1] else "unknown"
        scopes[scope] = scopes.get(scope, 0) + 1

    return scopes
