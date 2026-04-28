# reason_openai — SIGNATURE TOC

## PACK INFO

Target: P:\packages\cc-skills-meta\skills\reason_openai

Files: 9

## DIRECTORY INDEX

## SIGNATURE TOC

## APPENDIX: FULL IMPLEMENTATIONS

### hooks\reason_openai_analyze.py

- **load_entries**
  (path)
- **text_len**
  (value)
- **yes_no**
  (value)
- **summarize**
  (entries)
- **main**
### hooks\reason_openai_log.py

- **extract_section**
  (text,heading)
- **infer_mode**
  (route_text)
- **infer_depth**
  (route_text)
- **make_entry**
  (content)
- **main**
### hooks\reason_openai_pending_queue.py

- **load_last_log**
- **is_already_pending**
  (entry_id)
- **main**
### hooks\reason_openai_preflight.py

- **main**
### hooks\reason_openai_quality_gate.py

- **has_heading**
  (text,heading)
- **main**
### hooks\reason_openai_review_entry.py

- **load_jsonl**
  (path)
- **save_jsonl**
  (path,rows)
- **parse_bool**
  (value)
- **main**
### hooks\reason_openai_session_reminder.py

- **load_pending**
- **main**
### hooks\reason_openai_subagent_stop.py

- **detect_agent**
  (content)
- **check_sections**
  (content,sections)
- **main**
### reason_openai_router.py

- **Mode**

## APPENDIX: FULL SOURCE



---
## hooks\reason_openai_analyze.py

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



---
## hooks\reason_openai_log.py

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



---
## hooks\reason_openai_pending_queue.py

#!/usr/bin/env python3
"""
reason_openai_pending_queue.py — Write pending-review entries after /reason_openai log writes.

Every time a /reason_openai invocation is logged, this writes a lightweight pending entry
to reason_openai_pending.jsonl so the next session can nag without relying on memory.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LOG_DIR = Path.home() / ".claude" / "logs"
LOG_FILE = LOG_DIR / "reason_openai_log.jsonl"
PENDING_FILE = LOG_DIR / "reason_openai_pending.jsonl"


def load_last_log() -> dict | None:
    if not LOG_FILE.exists():
        return None
    try:
        with LOG_FILE.open("r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines:
            return None
        return json.loads(lines[-1])
    except Exception:
        return None


def is_already_pending(entry_id: str) -> bool:
    if not PENDING_FILE.exists():
        return False
    try:
        with PENDING_FILE.open("r", encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                item = json.loads(raw)
                if item.get("id") == entry_id and item.get("status") == "pending_review":
                    return True
    except Exception:
        pass
    return False


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

    last_entry = load_last_log()
    if not last_entry:
        print(json.dumps({"ok": True}))
        return 0

    entry_id = last_entry.get("id")
    if not entry_id or is_already_pending(entry_id):
        print(json.dumps({"ok": True}))
        return 0

    pending = {
        "id": entry_id,
        "created_at": last_entry.get("timestamp"),
        "status": "pending_review",
        "mode": last_entry.get("mode"),
        "depth": last_entry.get("depth"),
        "best_next_action": last_entry.get("best_next_action"),
        "best_current_conclusion": last_entry.get("best_current_conclusion"),
    }

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with PENDING_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(pending, ensure_ascii=False) + "\n")

    print(json.dumps({"ok": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


---
## hooks\reason_openai_preflight.py

#!/usr/bin/env python
"""
reason_openai_preflight.py — UserPromptSubmit preflight hook

Invoked when /reason_openai is detected in the prompt.
Injects a compact reminder of what decision-grade output requires.

Install by merging the hook config into ~/.claude/settings.json:
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/reason_openai_preflight.py"
          }
        ]
      }
    ]
  }
}
"""
from __future__ import annotations

import json
import sys


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        print(json.dumps({"ok": True}))
        return 0

    prompt = data.get("prompt", "") or ""

    if "/reason_openai" not in prompt:
        print(json.dumps({"ok": True}))
        return 0

    additional_context = """
For /reason_openai:
- Optimize for judgment, leverage, and outcome quality.
- Prefer strong recommendations over passive summaries.
- Include: conclusion, why it wins, strongest challenge, biggest uncertainty, next action, and ignore list when helpful.
- Preserve minority insights when high-impact.
- Prefer action over decorative analysis.
- If the user seems overwhelmed, reduce to: what matters, what doesn't, next move.
- If the user seems stuck, choose aggressively when justified.
- When tools, hooks, subagents, or MCP can materially improve truth, use them.
- Prefer one verified insight over five plausible guesses.
""".strip()

    print(json.dumps({
        "ok": True,
        "additionalContext": additional_context
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



---
## hooks\reason_openai_quality_gate.py

#!/usr/bin/env python
"""
reason_openai_quality_gate.py — Stop hook quality gate

Runs after /reason_openai answer is drafted.
Checks that the answer has decision-grade structure before Claude stops.

Required sections: Route chosen, Best current conclusion, Why it wins,
Strongest challenge, Biggest uncertainty, Best next action.

Install by merging the hook config into ~/.claude/settings.json:
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/reason_openai_quality_gate.py"
          }
        ]
      }
    ]
  }
}
"""
from __future__ import annotations

import json
import re
import sys

REQUIRED_HEADINGS = [
    "Route chosen",
    "Best current conclusion",
    "Why it wins",
    "Strongest challenge",
    "Biggest uncertainty",
    "Best next action",
]


def has_heading(text: str, heading: str) -> bool:
    pattern = rf"(?im)^##?\s*{re.escape(heading)}\s*$|(?im)^{re.escape(heading)}\s*$"
    return re.search(pattern, text) is not None


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        print(json.dumps({"ok": True}))
        return 0

    transcript = data.get("transcript_path")

    if not transcript:
        print(json.dumps({"ok": True}))
        return 0

    try:
        with open(transcript, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        print(json.dumps({"ok": True}))
        return 0

    if "/reason_openai" not in content:
        print(json.dumps({"ok": True}))
        return 0

    missing = [h for h in REQUIRED_HEADINGS if not has_heading(content, h)]

    if missing:
        print(json.dumps({
            "ok": False,
            "reason": (
                "Strengthen the /reason_openai answer before stopping. "
                f"Missing sections: {', '.join(missing)}."
            )
        }))
        return 0

    print(json.dumps({"ok": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



---
## hooks\reason_openai_review_entry.py

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


---
## hooks\reason_openai_session_reminder.py

#!/usr/bin/env python3
"""
reason_openai_session_reminder.py — SessionStart hook to surface pending /reason_openai reviews.

Reads reason_openai_pending.jsonl and injects a reminder into the session start
so the user gets nagged about unreviewed outcomes without having to remember manually.
"""
from __future__ import annotations

import json
from pathlib import Path

PENDING_FILE = Path.home() / ".claude" / "logs" / "reason_openai_pending.jsonl"


def load_pending() -> list[dict]:
    if not PENDING_FILE.exists():
        return []
    items = []
    try:
        with PENDING_FILE.open("r", encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                obj = json.loads(raw)
                if obj.get("status") == "pending_review":
                    items.append(obj)
    except Exception:
        pass
    return items


def main() -> int:
    items = load_pending()
    if not items:
        print(json.dumps({"ok": True}))
        return 0

    preview = items[-3:]
    bullets = []
    for item in preview:
        mode = item.get("mode") or "unknown"
        depth = item.get("depth") or "unknown"
        nxt = item.get("best_next_action") or "No next action recorded."
        bullets.append(f"- [{mode}/{depth}] {nxt}")

    additional = (
        f"You have {len(items)} pending /reason_openai review item(s). "
        "If useful, review the latest one and record outcome calibration.\n"
        + "\n".join(bullets)
    )

    print(json.dumps({
        "ok": True,
        "additionalContext": additional
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


---
## hooks\reason_openai_subagent_stop.py

#!/usr/bin/env python3
"""
SubagentStop quality gate for red_team, implementation_realist, decision_editor.
Verifies subagent outputs meet their contract before allowing stop.
"""
from __future__ import annotations
import json, re, sys
AGENT_MARKERS = ["red_team", "implementation_realist", "decision_editor"]
RED_TEAM_SECTIONS = ["Main objection", "Failure modes", "Hidden assumption", "What would change your mind", "Severity"]
IMPL_SECTIONS = ["Practical verdict", "Main implementation risk", "Operational burden", "Simplest viable version", "Recommendation"]
DECISION_SECTIONS = ["Best current conclusion", "Why it wins", "Strongest challenge", "Best next action", "Ignore"]
SECTION_MAP = {"red_team": RED_TEAM_SECTIONS, "implementation_realist": IMPL_SECTIONS, "decision_editor": DECISION_SECTIONS}

def detect_agent(content: str):
    content_lower = content.lower()
    for agent in AGENT_MARKERS:
        if agent in content_lower:
            return agent
    return None

def check_sections(content: str, sections: list[str]) -> list[str]:
    missing = []
    for section in sections:
        pattern = rf"(?im)^(?:##\s*)?{re.escape(section)}\s*$"
        if not any(re.search(pattern, line) for line in content.splitlines()):
            missing.append(section)
    return missing

def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        print(json.dumps({"ok": True}))
        return 0
    last_message = data.get("last_assistant_message", "") or ""
    if not last_message:
        print(json.dumps({"ok": True}))
        return 0
    agent = detect_agent(last_message)
    if not agent:
        print(json.dumps({"ok": True}))
        return 0
    missing = check_sections(last_message, SECTION_MAP.get(agent, []))
    if missing:
        reason = f"Strengthen {agent} output before stopping. Missing: " + ", ".join(missing)
        print(json.dumps({"ok": False, "reason": reason}))
        return 0
    print(json.dumps({"ok": True}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())


---
## reason_openai_router.py

#!/usr/bin/env python3
"""reason_openai_router.py — mode/depth router for /reason_openai."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Sequence

class Mode(str, Enum):
    REVIEW = "review"
    DESIGN = "design"
    DIAGNOSE = "diagnose"
    OPTIMIZE = "optimize"
    OFF = "off"
    DECIDE = "decide"
    EXECUTE = "execute"

class Depth(int, Enum):
    LOCAL = 0
    TARGETED = 1
    TRIBUNAL = 2

@dataclass
class ContextSignals:
    prompt: str
    cwd: str
    in_git_repo: bool
    has_code_indicators: bool
    has_error_indicators: bool
    has_perf_indicators: bool
    has_existing_solution_indicators: bool
    has_design_indicators: bool
    has_dissatisfaction_indicators: bool
    has_vague_uncertainty_indicators: bool

@dataclass
class DeficiencyScores:
    framing: int = 0
    confidence: int = 0
    evidence: int = 0
    option_space: int = 0
    decision: int = 0
    implementation: int = 0

REVIEW_PATTERNS = [r"\breview\b", r"\bcritique\b", r"\bpoke holes\b", r"\bnot convinced\b", r"\bunhappy\b", r"\bchallenge\b"]
DESIGN_PATTERNS = [r"\bdesign\b", r"\barchitecture\b", r"\bapproach\b", r"\bsolution\b", r"\bbrainstorm\b", r"\boptions\b"]
DIAGNOSE_PATTERNS = [r"\bbug\b", r"\berror\b", r"\bfailing\b", r"\broot cause\b", r"\bwhy is\b", r"\bbroken\b"]
OPTIMIZE_PATTERNS = [r"\boptimi[sz]e\b", r"\bperformance\b", r"\blatency\b", r"\bcost\b", r"\bimprove\b"]
OFF_PATTERNS = [r"\bfeels off\b", r"\bsomething feels off\b", r"\bmissing something\b", r"\bvague\b", r"\buneasy\b"]
CODE_PATTERNS = [r"```", r"\bfunction\b", r"\bclass\b", r"\bmethod\b", r"\bmodule\b", r"\bpatch\b"]
ERROR_PATTERNS = [r"\berror\b", r"\bexception\b", r"\btraceback\b", r"\bfailed\b", r"\bcrash\b"]
PERF_PATTERNS = [r"\bslow\b", r"\blatency\b", r"\bthroughput\b", r"\bmemory\b", r"\bcpu\b"]
EXISTING_SOLUTION_PATTERNS = [r"\bthis answer\b", r"\bthis solution\b", r"\bthis patch\b", r"\bthis design\b"]

MODE_FLAG_PATTERNS = {
    Mode.REVIEW: r"--mode\s+review\b",
    Mode.DESIGN: r"--mode\s+design\b",
    Mode.DIAGNOSE: r"--mode\s+diagnose\b",
    Mode.OPTIMIZE: r"--mode\s+optimize\b",
    Mode.OFF: r"--mode\s+off\b",
    Mode.DECIDE: r"--mode\s+decide\b",
    Mode.EXECUTE: r"--mode\s+execute\b",
}

def contains_any(text: str, patterns: Sequence[str]) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)

def in_git_repo(cwd: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"], cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=False
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except Exception:
        return False

def collect_context(prompt: str) -> ContextSignals:
    cwd = os.getcwd()
    return ContextSignals(
        prompt=prompt, cwd=cwd, in_git_repo=in_git_repo(cwd),
        has_code_indicators=contains_any(prompt, CODE_PATTERNS),
        has_error_indicators=contains_any(prompt, ERROR_PATTERNS),
        has_perf_indicators=contains_any(prompt, PERF_PATTERNS),
        has_existing_solution_indicators=contains_any(prompt, EXISTING_SOLUTION_PATTERNS),
        has_design_indicators=contains_any(prompt, DESIGN_PATTERNS),
        has_dissatisfaction_indicators=contains_any(prompt, REVIEW_PATTERNS),
        has_vague_uncertainty_indicators=contains_any(prompt, OFF_PATTERNS),
    )

def score_deficiencies(ctx: ContextSignals) -> DeficiencyScores:
    scores = DeficiencyScores()
    if ctx.has_vague_uncertainty_indicators:
        scores.framing += 2; scores.confidence += 2
    if ctx.has_dissatisfaction_indicators or ctx.has_existing_solution_indicators:
        scores.confidence += 3
    if ctx.has_error_indicators or ctx.has_code_indicators or ctx.has_perf_indicators:
        scores.evidence += 2; scores.implementation += 2
    if ctx.has_design_indicators:
        scores.option_space += 2; scores.decision += 1
    if contains_any(ctx.prompt, [r"\bwhich\b", r"\bchoose\b", r"\bbetter\b"]):
        scores.decision += 2
    return scores

def parse_mode_flags(prompt: str) -> Optional[Mode]:
    for mode, pattern in MODE_FLAG_PATTERNS.items():
        if re.search(pattern, prompt, re.IGNORECASE):
            return mode
    return None

def choose_mode(scores: DeficiencyScores, ctx: ContextSignals, forced: Optional[Mode] = None) -> Mode:
    if forced:
        return forced
    if ctx.has_vague_uncertainty_indicators and scores.framing >= 2:
        return Mode.OFF
    if ctx.has_error_indicators:
        return Mode.DIAGNOSE
    if ctx.has_perf_indicators:
        return Mode.OPTIMIZE
    if ctx.has_existing_solution_indicators or ctx.has_dissatisfaction_indicators:
        return Mode.REVIEW
    if ctx.has_design_indicators:
        return Mode.DESIGN
    ranked = {
        Mode.OFF: scores.framing + scores.confidence,
        Mode.REVIEW: scores.confidence + scores.implementation,
        Mode.DIAGNOSE: scores.evidence + scores.implementation,
        Mode.OPTIMIZE: scores.implementation + scores.decision,
        Mode.DESIGN: scores.option_space + scores.decision,
    }
    return max(ranked.items(), key=lambda x: x[1])[0]

def choose_depth(mode: Mode, scores: DeficiencyScores, ctx: ContextSignals) -> Depth:
    if mode == Mode.OFF and scores.confidence >= 3:
        return Depth.TARGETED
    if mode in {Mode.REVIEW, Mode.DESIGN} and (scores.confidence >= 3 or scores.option_space >= 2):
        return Depth.TARGETED
    if mode in {Mode.DIAGNOSE, Mode.OPTIMIZE} and (ctx.has_code_indicators or ctx.in_git_repo):
        return Depth.TARGETED
    if scores.confidence >= 3 and (scores.option_space >= 2 or scores.implementation >= 2):
        return Depth.TRIBUNAL
    return Depth.LOCAL

def route_explanation(mode: Mode, ctx: ContextSignals) -> str:
    reasons = []
    if ctx.has_existing_solution_indicators: reasons.append("existing solution detected")
    if ctx.has_dissatisfaction_indicators: reasons.append("dissatisfaction detected")
    if ctx.has_error_indicators: reasons.append("error symptoms present")
    if ctx.has_perf_indicators: reasons.append("performance cues present")
    if ctx.has_design_indicators: reasons.append("design cues present")
    if ctx.has_vague_uncertainty_indicators: reasons.append("vague uncertainty detected")
    reason_text = ", ".join(reasons) if reasons else "general reasoning requested"
    return f"Routed to {mode.value} because {reason_text}."

def build_local_reasoning_prompt(prompt: str, mode: Mode) -> str:
    guidance = {
        Mode.REVIEW: "Review the existing answer or solution. Surface hidden flaws, missed tradeoffs, and implementation risk.",
        Mode.DESIGN: "Expand the solution space, compare strong options, and recommend a path.",
        Mode.DIAGNOSE: "Generate hypotheses, identify the smallest discriminating check, and rank likely causes.",
        Mode.OPTIMIZE: "Clarify the objective function, identify true bottlenecks, and separate local tweaks from structural improvements.",
        Mode.OFF: "Do not answer directly. Identify what assumption may be wrong, what is missing, and what question should be asked instead.",
        Mode.DECIDE: "Force a clear recommendation. Name the best option, why it wins, its strongest challenge, and what would change the decision.",
        Mode.EXECUTE: "Move from thought to action. Identify the immediate next step and the concrete blockers to shipping.",
    }[mode]
    return (
        f"You are /reason_openai local controller.\n"
        f"Mode: {mode.value}\n"
        f"Goal: {guidance}\n\n"
        f"User prompt:\n{prompt}\n\n"
        "Return these exact sections:\n"
        "Route chosen:\n"
        "Best current conclusion:\n"
        "Why it wins:\n"
        "Strongest challenge:\n"
        "Biggest uncertainty:\n"
        "Best next action:\n"
        "Ignore:\n"
        "Minority warning:\n"
    )

def parse_sections(text: str) -> Dict[str, str]:
    labels = ["Route chosen:", "Best current conclusion:", "Why it wins:",
             "Strongest challenge:", "Biggest uncertainty:", "Best next action:", "Ignore:", "Minority warning:"]
    sections = {label[:-1]: "" for label in labels}
    current_key = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        matched = False
        for label in labels:
            if line.startswith(label):
                current_key = label[:-1]
                value = line[len(label):].strip()
                if value:
                    sections[current_key] = value
                matched = True
                break
        if not matched and current_key:
            sections[current_key] = (sections[current_key] + "\n" + line).strip()
    return sections

def format_result(sections: Dict[str, str], mode: Mode, why: str) -> str:
    parts = [
        f"Route chosen:\n{why}",
        f"Best current conclusion:\n{sections.get('Best current conclusion', 'No conclusion produced.')}",
        f"Why it wins:\n{sections.get('Why it wins', 'No reasoning produced.')}",
        f"Strongest challenge:\n{sections.get('Strongest challenge', 'No challenge produced.')}",
        f"Biggest uncertainty:\n{sections.get('Biggest uncertainty', 'No uncertainty produced.')}",
        f"Best next action:\n{sections.get('Best next action', 'No next action produced.')}",
    ]
    if sections.get("Ignore"):
        parts.append(f"Ignore:\n{sections['Ignore']}")
    if sections.get("Minority warning"):
        parts.append(f"Minority warning:\n{sections['Minority warning']}")
    return "\n\n".join(parts)

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="/reason_openai router")
    parser.add_argument("--prompt", default="", help="Prompt to reason about")
    parser.add_argument("--mode", default="", help="Force mode: review, design, diagnose, optimize, off, decide, execute")
    parser.add_argument("--depth", default="", help="Force depth: local, targeted, tribunal")
    args = parser.parse_args(argv)

    prompt = args.prompt.strip()
    if not prompt:
        print("No prompt provided.")
        return 1

    forced_mode = None
    if args.mode:
        try:
            forced_mode = Mode(args.mode.lower())
        except ValueError:
            print(f"Unknown mode: {args.mode}")
            return 1

    forced_depth = None
    if args.depth:
        depth_map = {"local": Depth.LOCAL, "targeted": Depth.TARGETED, "tribunal": Depth.TRIBUNAL}
        forced_depth = depth_map.get(args.depth.lower())
        if forced_depth is None:
            print(f"Unknown depth: {args.depth}")
            return 1

    ctx = collect_context(prompt)
    scores = score_deficiencies(ctx)
    mode = choose_mode(scores, ctx, forced_mode)
    depth = forced_depth or choose_depth(mode, scores, ctx)
    why = route_explanation(mode, ctx)

    if depth == Depth.LOCAL:
        local_prompt = build_local_reasoning_prompt(prompt, mode)
        sys.stdout.write(local_prompt)
        return 0

    sys.stdout.write(
        f"Route chosen:\n{why}\n\n"
        f"Mode: {mode.value}\n"
        f"Depth: {depth.value}\n\n"
        f"For depth {depth.value}, invoke subagents:\n"
        f"- red_team (attack the conclusion)\n"
        f"- implementation_realist (pressure-test practicality)\n"
        f"- decision_editor (compress to final recommendation)\n\n"
        f"Local reasoning prompt:\n{build_local_reasoning_prompt(prompt, mode)}"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
