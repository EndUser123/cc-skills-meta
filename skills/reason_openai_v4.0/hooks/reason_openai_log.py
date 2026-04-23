#!/usr/bin/env python
"""
reason_openai_log.py — Stop hook usage logger with outcome calibration fields.

Logs every /reason_openai invocation to ~/.claude/logs/reason_openai_log.jsonl.
Each entry includes both the output structure and placeholder fields for
manual outcome calibration (acted_on, was_directionally_correct, outcome_quality,
biggest_miss, time_to_action_minutes, review_notes).

Install by adding to the Stop hook chain in ~/.claude/settings.json:
{
  "hooks": {
    "Stop": [
      {"command": "python ~/.claude/hooks/reason_openai_quality_gate.py"},
      {"command": "python ~/.claude/hooks/reason_openai_log.py"}
    ]
  }
}
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path.home() / ".claude" / "logs"
LOG_FILE = LOG_DIR / "reason_openai_log.jsonl"

HEADINGS = [
    "Route chosen",
    "Best current conclusion",
    "Why it wins",
    "Strongest challenge",
    "Biggest uncertainty",
    "Best next action",
    "Ignore",
    "Minority warning",
]


def extract_section(text: str, heading: str) -> str | None:
    pattern = rf"(?ims)^(?:##\s*)?{re.escape(heading)}\s*$\n(.*?)(?=^(?:##\s*)?[A-Z][^\n]*\s*$|\Z)"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip() or None
    return None


def infer_mode(route_text: str) -> str | None:
    route_text = (route_text or "").lower()
    for mode in ["review", "design", "diagnose", "optimize", "decide", "explore", "off", "execute"]:
        if mode in route_text:
            return mode
    return None


def infer_depth(route_text: str) -> str | None:
    route_text = (route_text or "").lower()
    for depth in ["auto", "deep", "board", "maximal"]:
        if depth in route_text:
            return depth
    return None


def make_entry(content: str) -> dict:
    sections = {heading: extract_section(content, heading) for heading in HEADINGS}
    route = sections.get("Route chosen") or ""

    return {
        "id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "route_text": route,
        "mode": infer_mode(route),
        "depth": infer_depth(route),
        "best_current_conclusion": sections.get("Best current conclusion"),
        "why_it_wins": sections.get("Why it wins"),
        "strongest_challenge": sections.get("Strongest challenge"),
        "biggest_uncertainty": sections.get("Biggest uncertainty"),
        "best_next_action": sections.get("Best next action"),
        "ignore": sections.get("Ignore"),
        "minority_warning": sections.get("Minority warning"),
        "acted_on": None,
        "was_directionally_correct": None,
        "outcome_quality": None,
        "biggest_miss": None,
        "time_to_action_minutes": None,
        "review_notes": None,
    }


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        print(json.dumps({"ok": True}))
        return 0

    transcript_path = data.get("transcript_path")
    if not transcript_path:
        print(json.dumps({"ok": True}))
        return 0

    try:
        content = Path(transcript_path).read_text(encoding="utf-8")
    except Exception:
        print(json.dumps({"ok": True}))
        return 0

    if "/reason_openai" not in content:
        print(json.dumps({"ok": True}))
        return 0

    entry = make_entry(content)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(json.dumps({"ok": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
