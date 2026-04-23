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