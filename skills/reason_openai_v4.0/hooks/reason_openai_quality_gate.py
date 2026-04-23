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
