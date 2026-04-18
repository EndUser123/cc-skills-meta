#!/usr/bin/env python3
"""
Presents proposed changes for user review with interactive approval.

v1.4.0: Added queue processing workflow before signal review
v1.3.0: Added meta-learning feedback logging (passive, non-blocking)
"""

import difflib
import sqlite3
from pathlib import Path
from typing import Any

# Meta-learning integration (optional, passive)
try:
    from meta_learning import log_feedback

    META_LEARNING_AVAILABLE = True
except ImportError:
    META_LEARNING_AVAILABLE = False

# Queue integration
import scope_analyzer
from learning_ledger import LearningLedger
from promote_learning import LearningPromoter


def process_queue_interactive() -> int:
    """
    Process pending queue items interactively.

    Shows queue items one by one and asks user to approve/skip/quit.
    Approved items are marked as promoted.

    Returns:
        Number of items approved, or 0 if queue is empty or user skipped.
    """
    ledger = LearningLedger()
    stats = ledger.get_stats()
    pending_count = stats.get("by_status", {}).get("pending", 0)

    if pending_count == 0:
        return 0

    # Query pending learnings
    rows = _query_pending_learnings(ledger.db_path)

    if not rows:
        return 0

    approved_count = 0

    print("\n" + "=" * 60)
    print("QUEUE PROCESSING")
    print("=" * 60 + "\n")
    print(f"Found {pending_count} pending learning(s) in queue\n")

    for idx, row in enumerate(rows, 1):
        fingerprint = row["fingerprint"]
        content = row["content"]
        confidence = row["confidence"]
        skill_name = row["skill_name"] or "unknown"

        # Analyze scope for this learning
        try:
            scope_analysis = scope_analyzer.analyze_learning(content, skill_name)
            recommended_scope = scope_analysis.get("recommended_scope", "skill")
            # Map scope: "skill" → "project", "global" → "global"
            display_scope = "project" if recommended_scope == "skill" else recommended_scope

            # Determine target files based on scope
            if display_scope == "global":
                display_target = "~/.claude/CLAUDE.md"
            else:
                display_target = f"~/.claude/skills/{skill_name}/SKILL.md"
        except Exception:
            # Fallback if scope analysis fails
            display_scope = "unknown"
            display_target = "Unknown"

        # Truncate content for display
        display_content = content[:100] + "..." if len(content) > 100 else content

        print(f"[{idx}/{len(rows)}] Item: {fingerprint[:8]}...")
        print(f"  Content: {display_content}")
        print(f"  Confidence: {confidence:.0%}")
        print(f"  Skill: {skill_name}")
        print(f"  Scope: {display_scope}")
        print(f"  Target: {display_target}")
        print()

        response = input("[A]pprove / [S]kip / [Q]uit queue processing? ").strip().upper()

        if response == "A" or response == "":
            # Approve - mark as promoted and sync to files
            try:
                # First mark as promoted in ledger
                ledger.mark_promoted(fingerprint, reason="User approved during queue processing")

                # Then sync to CLAUDE.md using promote_learning
                promoter = LearningPromoter()
                promote_result = promoter.promote(fingerprint)

                if promote_result.get("success"):
                    approved_count += 1
                    print(
                        f"  ✓ Approved and synced to {promote_result.get('added_to', 'CLAUDE.md')}\n"
                    )
                else:
                    print(
                        f"  ⚠ Approved but sync failed: {promote_result.get('error', 'Unknown error')}\n"
                    )
                    approved_count += 1  # Still count as approved even if sync fails
            except Exception as e:
                print(f"  ✗ Error promoting: {e}\n")

        elif response == "Q":
            print(f"  ⊘ Quitting queue processing ({approved_count} approved)\n")
            break

        else:  # Skip
            print("  ⊘ Skipped\n")

    if approved_count > 0:
        print(f"✓ Processed {approved_count} item(s) from queue")

    return approved_count


def _query_pending_learnings(db_path: str) -> list[sqlite3.Row]:
    """
    Query pending learnings from the database.

    Args:
        db_path: Path to the SQLite database.

    Returns:
        List of database rows containing pending learnings.
    """
    query = """
        SELECT fingerprint, content, confidence, skill_name, status
        FROM learnings
        WHERE status = 'pending'
        ORDER BY confidence DESC
    """

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()
    except Exception:
        # Return empty list on error
        return []


def present_review(signals_by_skill: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """
    Present signals and proposed changes for approval.
    Returns list of approved changes.

    Workflow:
    1. Check for pending queue items
    2. If pending items exist, ask user to process queue first
    3. If user agrees, process queue interactively
    4. Continue with normal signal review
    """
    if not signals_by_skill:
        return []

    # Step 1: Check for pending queue items
    ledger = LearningLedger()
    stats = ledger.get_stats()
    pending_count = stats.get("by_status", {}).get("pending", 0)

    # Step 2: Ask user if they want to process queue first
    if pending_count > 0:
        print("\n" + "=" * 60)
        print("QUEUE DETECTED")
        print("=" * 60 + "\n")
        print(f"You have {pending_count} pending learning(s) in the queue.")

        response = (
            input("Process queue items before reviewing new signals? [Y]es / [N]o: ")
            .strip()
            .upper()
        )

        if response == "Y" or response == "":
            # Step 3: Process queue interactively
            approved_count = process_queue_interactive()
            print()  # Blank line for separation

    # Step 4: Continue with normal signal review
    print("\n" + "=" * 60)
    print("REFLECTION REVIEW")
    print("=" * 60 + "\n")

    # Show summary
    print("## Signals Detected\n")
    for skill, signals in signals_by_skill.items():
        high = len([s for s in signals if s.get("confidence") == "HIGH"])
        medium = len([s for s in signals if s.get("confidence") == "MEDIUM"])
        low = len([s for s in signals if s.get("confidence") == "LOW"])
        print(f"**{skill}**:")
        item_num = 1
        if high:
            print(f"  {item_num}. HIGH: {high} corrections")
            item_num += 1
        if medium:
            print(f"  {item_num}. MEDIUM: {medium} approvals")
            item_num += 1
        if low:
            print(f"  {item_num}. LOW: {low} observations")
            item_num += 1

    print("\n" + "-" * 60 + "\n")

    approved_changes = []

    for skill_name, signals in signals_by_skill.items():
        print(f"\n## {skill_name}\n")

        # Generate proposed changes
        proposed = generate_proposed_changes(skill_name, signals)

        if (
            not proposed["high_confidence"]
            and not proposed["medium_confidence"]
            and not proposed["low_confidence"]
        ):
            print("No actionable changes proposed for this skill.\n")
            continue

        # Show diff
        show_diff(skill_name, proposed)

        # Get approval
        response = input("\n[A]pprove / [M]odify / [S]kip / [Q]uit? ").strip().upper()

        if response == "A" or response == "":
            approved_changes.append(
                {"skill_name": skill_name, "signals": signals, "proposed_updates": proposed}
            )
            print(f"✓ Approved changes to {skill_name}")

            # Meta-learning: log acceptance (passive, non-blocking)
            _log_decision(signals, skill_name, "accept")

        elif response == "M":
            # Natural language modification
            modification = input("Describe modification: ").strip()
            if modification:
                modified = apply_modification(proposed, modification)
                approved_changes.append(
                    {"skill_name": skill_name, "signals": signals, "proposed_updates": modified}
                )
                print(f"✓ Applied modified changes to {skill_name}")

                # Meta-learning: log modification
                _log_decision(signals, skill_name, "modify", modification)
            else:
                print(f"⊘ Skipped {skill_name} (no modification provided)")
                _log_decision(signals, skill_name, "skip")

        elif response == "Q":
            print("Review aborted")
            _log_decision(signals, skill_name, "quit")
            return []

        else:  # Skip
            print(f"⊘ Skipped {skill_name}")
            _log_decision(signals, skill_name, "skip")

    return approved_changes


def _log_decision(signals: list[dict], skill_name: str, decision: str, modification: str = None):
    """
    Log decision to meta-learning system.

    This is completely passive and non-blocking.
    Failures are silently ignored to never break core workflow.
    """
    if not META_LEARNING_AVAILABLE:
        return

    try:
        for signal in signals:
            log_feedback(
                pattern_type=signal.get("type", "unknown"),
                pattern_regex=signal.get("detection_method", "regex"),
                skill_name=skill_name,
                confidence_level=signal.get("confidence", "UNKNOWN"),
                decision=decision,
                signal_content=signal.get("content", ""),
                modification=modification,
            )
    except Exception:
        # Silent fail - meta-learning should never break core workflow
        pass


def generate_proposed_changes(
    skill_name: str, signals: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """Generate proposed skill updates from signals"""
    updates = {"high_confidence": [], "medium_confidence": [], "low_confidence": []}

    for signal in signals:
        confidence = signal.get("confidence", "LOW")

        if confidence == "HIGH":
            updates["high_confidence"].append(
                {
                    "description": extract_correction_description(signal),
                    "old_approach": extract_old_approach(signal),
                    "new_approach": extract_new_approach(signal),
                }
            )
        elif confidence == "MEDIUM":
            updates["medium_confidence"].append(
                {
                    "pattern": extract_pattern_name(signal),
                    "description": extract_pattern_description(signal),
                }
            )
        else:  # LOW
            updates["low_confidence"].append(
                {"suggestion": signal.get("suggestion", signal.get("description", "Unknown"))}
            )

    return updates


def extract_correction_description(signal: dict[str, Any]) -> str:
    """Extract description from correction signal"""
    if "description" in signal:
        return signal["description"]

    content = signal.get("content", "")
    match = signal.get("match", ())

    if match and len(match) >= 2:
        return f"Use '{match[1]}' instead of '{match[0]}'"
    elif match and len(match) == 1:
        return f"Correction: {match[0]}"

    return "User provided correction"


def extract_old_approach(signal: dict[str, Any]) -> str:
    """Extract old approach from signal"""
    match = signal.get("match", ())
    if match and len(match) >= 1:
        return str(match[0])[:100]  # Limit length

    # Try to extract from content
    content = signal.get("content", "")
    return content[:100]


def extract_new_approach(signal: dict[str, Any]) -> str:
    """Extract new approach from signal"""
    match = signal.get("match", ())
    if match and len(match) >= 2:
        return str(match[1])[:100]  # Limit length

    # Fallback to content
    content = signal.get("content", "")
    return content[:100]


def extract_pattern_name(signal: dict[str, Any]) -> str:
    """Extract pattern name from approval signal"""
    return signal.get("type", "approval").capitalize()


def extract_pattern_description(signal: dict[str, Any]) -> str:
    """Extract pattern description from approval signal"""
    if "description" in signal:
        return signal["description"]

    previous = signal.get("previous_approach", "")
    if previous:
        return f"Approved approach: {previous[:100]}"

    return "Approved user's approach"


def show_diff(skill_name: str, proposed_updates: dict[str, list[dict[str, Any]]]):
    """Show unified diff of proposed changes"""
    skill_path = Path.home() / ".claude" / "skills" / skill_name / "SKILL.md"

    if not skill_path.exists():
        print(f"Skill file not found: {skill_path}")
        return

    try:
        with open(skill_path) as f:
            original = f.read()

        # Simulate applying updates
        from update_skill import (
            apply_high_confidence_update,
            apply_low_confidence_update,
            apply_medium_confidence_update,
            parse_skill_file,
            reconstruct_skill_file,
        )

        frontmatter, body = parse_skill_file(original)

        # Apply proposed changes
        for update in proposed_updates.get("high_confidence", []):
            body = apply_high_confidence_update(body, update)

        for update in proposed_updates.get("medium_confidence", []):
            body = apply_medium_confidence_update(body, update)

        for update in proposed_updates.get("low_confidence", []):
            body = apply_low_confidence_update(body, update)

        updated = reconstruct_skill_file(frontmatter, body)

        # Generate diff
        diff = list(
            difflib.unified_diff(
                original.splitlines(keepends=True),
                updated.splitlines(keepends=True),
                fromfile=f"{skill_name}/SKILL.md (current)",
                tofile=f"{skill_name}/SKILL.md (proposed)",
                lineterm="",
            )
        )

        if diff:
            print("\n```diff")
            for line in diff[:100]:  # Limit to first 100 lines
                print(line.rstrip())
            if len(diff) > 100:
                print(f"\n... ({len(diff) - 100} more lines)")
            print("```\n")
        else:
            print("\nNo changes to display.\n")

    except Exception as e:
        print(f"Error generating diff: {e}")


def apply_modification(
    proposed: dict[str, list[dict[str, Any]]], user_instruction: str
) -> dict[str, list[dict[str, Any]]]:
    """Apply natural language modification to proposed changes"""
    # For now, this is a placeholder
    # In a full implementation, this would use Claude to interpret the modification
    print(f"Note: Natural language modification '{user_instruction}' would be applied here")
    print("(This feature requires Claude integration - using original proposal for now)")
    return proposed


if __name__ == "__main__":
    # Test mode
    test_signals = {
        "test-skill": [
            {
                "confidence": "HIGH",
                "type": "correction",
                "content": "No, don't use X, use Y instead",
                "match": ("X", "Y"),
                "description": "Use Y instead of X",
            },
            {
                "confidence": "MEDIUM",
                "type": "approval",
                "description": "Approved this approach",
                "previous_approach": "Used pattern Z successfully",
            },
        ]
    }

    approved = present_review(test_signals)
    print(f"\nApproved {len(approved)} change(s)")
