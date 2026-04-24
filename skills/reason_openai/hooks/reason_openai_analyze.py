#!/usr/bin/env python
"""
reason_openai_analyze.py — Calibration log analyzer

Reads ~/.claude/logs/reason_openai_log.jsonl and prints a summary:
- mode / depth distribution
- field completeness (% present, avg length)
- quality heuristics (missing sections)
- outcome heuristics (if logged)
- top repeated misses
- lightweight recommendations

Run directly:
    python ~/.claude/hooks/reason_openai_analyze.py

Or via the slash command:
    /reason_openai_analyze
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

LOG_FILE = Path.home() / ".claude" / "logs" / "reason_openai_log.jsonl"


def load_entries(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    entries: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    entries.append(obj)
            except json.JSONDecodeError:
                print(f"[warn] Skipping invalid JSON on line {line_no}")
    return entries


def text_len(value: Any) -> int:
    return len(str(value).strip()) if value else 0


def yes_no(value: bool | None) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "unknown"


def summarize(entries: list[dict[str, Any]]) -> str:
    total = len(entries)
    if total == 0:
        return "No reason_openai log entries found."

    mode_counts = Counter()
    depth_counts = Counter()

    missing_counts: dict[str, int] = Counter()
    field_lengths: dict[str, list[int]] = defaultdict(list)

    acted_on_counts = Counter()
    correct_counts = Counter()
    outcome_scores: list[float] = []
    time_to_action: list[float] = []

    biggest_miss_counter = Counter()
    challenge_empty = 0
    ignore_empty = 0
    minority_empty = 0

    for entry in entries:
        mode_counts[entry.get("mode") or "unknown"] += 1
        depth_counts[entry.get("depth") or "unknown"] += 1

        for field in [
            "best_current_conclusion",
            "why_it_wins",
            "strongest_challenge",
            "biggest_uncertainty",
            "best_next_action",
            "ignore",
            "minority_warning",
        ]:
            value = entry.get(field)
            if value:
                field_lengths[field].append(text_len(value))
            else:
                missing_counts[field] += 1

        if not entry.get("strongest_challenge"):
            challenge_empty += 1
        if not entry.get("ignore"):
            ignore_empty += 1
        if not entry.get("minority_warning"):
            minority_empty += 1

        if "acted_on" in entry:
            acted_on_counts[yes_no(entry.get("acted_on"))] += 1
        if "was_directionally_correct" in entry:
            correct_counts[yes_no(entry.get("was_directionally_correct"))] += 1

        oq = entry.get("outcome_quality")
        if isinstance(oq, (int, float)):
            outcome_scores.append(float(oq))

        tta = entry.get("time_to_action_minutes")
        if isinstance(tta, (int, float)):
            time_to_action.append(float(tta))

        biggest_miss = (entry.get("biggest_miss") or "").strip()
        if biggest_miss:
            biggest_miss_counter[biggest_miss] += 1

    lines: list[str] = []

    lines.append("reason_openai log summary")
    lines.append("=" * 28)
    lines.append(f"entries: {total}")
    lines.append("")

    lines.append("mode distribution")
    lines.append("-" * 17)
    for mode, count in mode_counts.most_common():
        lines.append(f"{mode:>12}: {count}")
    lines.append("")

    lines.append("depth distribution")
    lines.append("-" * 18)
    for depth, count in depth_counts.most_common():
        lines.append(f"{depth:>12}: {count}")
    lines.append("")

    lines.append("field completeness")
    lines.append("-" * 18)
    tracked_fields = [
        "best_current_conclusion",
        "why_it_wins",
        "strongest_challenge",
        "biggest_uncertainty",
        "best_next_action",
        "ignore",
        "minority_warning",
    ]
    for field in tracked_fields:
        present = total - missing_counts[field]
        pct = (present / total) * 100
        avg_len = round(mean(field_lengths[field]), 1) if field_lengths[field] else 0
        lines.append(f"{field:>24}: present={present:>4}/{total} ({pct:5.1f}%), avg_len={avg_len}")
    lines.append("")

    lines.append("quality heuristics")
    lines.append("-" * 18)
    lines.append(f"missing strongest_challenge: {challenge_empty}/{total}")
    lines.append(f"missing ignore section     : {ignore_empty}/{total}")
    lines.append(f"missing minority warning   : {minority_empty}/{total}")
    lines.append("")

    if acted_on_counts:
        lines.append("acted_on")
        lines.append("-" * 8)
        for key, count in acted_on_counts.most_common():
            lines.append(f"{key:>12}: {count}")
        lines.append("")

    if correct_counts:
        lines.append("directionally_correct")
        lines.append("-" * 21)
        for key, count in correct_counts.most_common():
            lines.append(f"{key:>12}: {count}")
        lines.append("")

    if outcome_scores:
        lines.append("outcome quality")
        lines.append("-" * 15)
        lines.append(f"average score: {mean(outcome_scores):.2f}")
        lines.append(f"min score    : {min(outcome_scores):.2f}")
        lines.append(f"max score    : {max(outcome_scores):.2f}")
        lines.append("")

    if time_to_action:
        lines.append("time to action")
        lines.append("-" * 14)
        lines.append(f"average minutes: {mean(time_to_action):.1f}")
        lines.append(f"fastest        : {min(time_to_action):.1f}")
        lines.append(f"slowest        : {max(time_to_action):.1f}")
        lines.append("")

    if biggest_miss_counter:
        lines.append("top repeated misses")
        lines.append("-" * 19)
        for miss, count in biggest_miss_counter.most_common(10):
            lines.append(f"{count:>3}  {miss}")
        lines.append("")

    lines.append("recommended adjustments")
    lines.append("-" * 22)

    recommendations: list[str] = []

    if challenge_empty / total > 0.2:
        recommendations.append("Strengthen enforcement for 'Strongest challenge' in the Stop hook or command template.")
    if ignore_empty / total > 0.35:
        recommendations.append("Encourage 'Ignore' more often; useful for ADHD/noise reduction.")
    if minority_empty / total > 0.6:
        recommendations.append("Minority warnings underused; prompt more explicitly for low-consensus risks.")
    if mode_counts.get("decide", 0) > 0 and depth_counts.get("board", 0) == 0:
        recommendations.append("Consider --depth board more often for important decisions.")
    if outcome_scores and mean(outcome_scores) < 3.5:
        recommendations.append("Average outcome quality is mediocre; tighten route selection or execution guidance.")
    if time_to_action and mean(time_to_action) > 60:
        recommendations.append("Time-to-action is high; bias toward smaller, lower-friction next steps.")
    if not recommendations:
        recommendations.append("No obvious structural issue detected. Keep logging and review after more entries.")

    for rec in recommendations:
        lines.append(f"- {rec}")

    return "\n".join(lines)


def main() -> int:
    entries = load_entries(LOG_FILE)
    print(summarize(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
