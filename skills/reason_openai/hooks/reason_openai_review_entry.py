#!/usr/bin/env python3
"""
reason_openai_review_entry.py — Update a log entry with outcome calibration data.

Also marks the corresponding pending entry as "reviewed" in reason_openai_pending.jsonl.

Usage:
    python ~/.claude/hooks/reason_openai_review_entry.py --id <entry_id> [fields...]
    python ~/.claude/hooks/reason_openai_review_entry.py [fields...]   # updates latest entry

Fields:
    --acted-on yes|no|true|false
    --correct yes|no|true|false
    --outcome-quality 1|2|3|4|5
    --biggest-miss "description"
    --time-to-action N         (minutes)
    --review-notes "free text"

Examples:
    python ~/.claude/hooks/reason_openai_review_entry.py --acted-on yes --correct yes --outcome-quality 4
    python ~/.claude/hooks/reason_openai_review_entry.py --biggest-miss "underestimated migration risk" --time-to-action 15
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "logs" / "reason_openai_log.jsonl"
PENDING_FILE = Path.home() / ".claude" / "logs" / "reason_openai_pending.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def save_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_bool(value: str | None):
    if value is None:
        return None
    v = value.strip().lower()
    if v in {"yes", "y", "true", "1"}:
        return True
    if v in {"no", "n", "false", "0"}:
        return False
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Update a reason_openai log entry with outcome data.")
    parser.add_argument("--id", help="Entry id to update; defaults to latest.")
    parser.add_argument("--acted-on", help="Did you act on it? (yes/no/true/false)")
    parser.add_argument("--correct", help="Was it directionally correct? (yes/no/true/false)")
    parser.add_argument("--outcome-quality", type=int, choices=[1, 2, 3, 4, 5],
                        help="Outcome quality 1–5")
    parser.add_argument("--biggest-miss", help="What was the biggest miss?")
    parser.add_argument("--time-to-action", type=int, dest="time_to_action",
                        help="Minutes from answer to first action")
    parser.add_argument("--review-notes", help="Free-text review notes")
    args = parser.parse_args()

    entries = load_jsonl(LOG_FILE)
    if not entries:
        print("No log entries found.")
        return 1

    target: dict | None = None
    if args.id:
        for entry in reversed(entries):
            if entry.get("id") == args.id:
                target = entry
                break
        if target is None:
            print(f"Entry id not found: {args.id}")
            return 1
    else:
        target = entries[-1]

    if args.acted_on is not None:
        target["acted_on"] = parse_bool(args.acted_on)
    if args.correct is not None:
        target["was_directionally_correct"] = parse_bool(args.correct)
    if args.outcome_quality is not None:
        target["outcome_quality"] = args.outcome_quality
    if args.biggest_miss is not None:
        target["biggest_miss"] = args.biggest_miss
    if args.time_to_action is not None:
        target["time_to_action_minutes"] = args.time_to_action
    if args.review_notes is not None:
        target["review_notes"] = args.review_notes

    save_jsonl(LOG_FILE, entries)

    # Mark corresponding pending entry as reviewed
    target_id = target.get("id")
    pending = load_jsonl(PENDING_FILE)
    changed = False
    for item in pending:
        if item.get("id") == target_id and item.get("status") == "pending_review":
            item["status"] = "reviewed"
            changed = True
    if changed:
        save_jsonl(PENDING_FILE, pending)

    print("Updated entry:")
    print(json.dumps({
        "id": target.get("id"),
        "acted_on": target.get("acted_on"),
        "was_directionally_correct": target.get("was_directionally_correct"),
        "outcome_quality": target.get("outcome_quality"),
        "biggest_miss": target.get("biggest_miss"),
        "time_to_action_minutes": target.get("time_to_action_minutes"),
        "review_notes": target.get("review_notes"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())