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