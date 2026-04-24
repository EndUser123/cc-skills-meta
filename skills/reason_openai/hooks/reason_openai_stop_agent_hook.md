---
description: Agent-based Stop quality verifier — replaces the prompt-only gate with substantive judgment.
allowed-tools: Bash(python:*)
---

# reason_openai Stop Agent Hook

A `Stop` **agent** hook that spawns a verifier subagent to judge whether the `/reason_openai` output is decision-grade before allowing completion.

## Why agent is better than regex

| Regex gate | Agent verifier |
|------------|----------------|
| "did headings exist?" | "did it actually choose?" |
| token presence check | "is the challenge real?" |
| no substance check | "is the next action concrete?" |
| no bloat check | "is this too fluffy?" |
| no minority check | "did it miss a minority warning?" |

## How It Works

1. Runs as the **first** Stop hook — before log and pending queue
2. Spawns a verifier agent with `last_assistant_message` from the hook input
3. Agent checks substance and structure, not just heading presence
4. If quality is insufficient, blocks completion and returns a specific reason
5. Uses `stop_hook_active` to avoid infinite polish loops

## Install

Replace the prompt-based Stop entry in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "agent",
            "prompt": "You are the final quality verifier for /reason_openai. The hook input JSON is: $ARGUMENTS\n\nUse `last_assistant_message` as the main artifact. If needed, inspect the transcript for the immediate turn only.\n\nIf this is not a /reason_openai turn, return exactly JSON: {\"ok\": true}.\n\nIf this is a /reason_openai turn, verify the final answer meets all of these:\n1. It clearly states a recommendation or conclusion.\n2. It includes a real strongest challenge.\n3. It states the biggest remaining uncertainty.\n4. It gives a concrete next action.\n5. It is not bloated or padded.\n6. It does not flatten an important minority concern.\n\nRequired sections:\n- Route chosen\n- Best current conclusion\n- Why it wins\n- Strongest challenge\n- Biggest uncertainty\n- Best next action\n\nIf any required section is missing or weak, return exactly JSON: {\"ok\": false, \"reason\": \"Strengthen the /reason_openai answer before stopping. Add/fix: <very short specific correction>.\"}\n\nIf the answer is good enough, return exactly JSON: {\"ok\": true}.\n\nIf stop_hook_active is true and the answer is already reasonably decision-grade, return {\"ok\": true} rather than demanding more polishing.",
            "timeout": 90
          },
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/reason_openai_log.py"
          },
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/reason_openai_pending_queue.py"
          }
        ]
      }
    ]
  }
}
```

## Quality Dimensions Judged

| Dimension | What the verifier checks |
|-----------|------------------------|
| **Chosen** | Does it commit to a direction, not hide behind vague neutrality? |
| **Challenged** | Is the strongest challenge substantive — a real objection, not a token one? |
| **Uncertainty** | Does it state the biggest remaining uncertainty honestly? |
| **Actionable** | Is the next action concrete and friction-aware? |
| **Not bloated** | Is length proportionate to decision weight? |
| **Minority-preserved** | Did it suppress an important minority concern? |

## Stop Chain Order

```
Stop:
  1. agent (quality gate)     ← blocks if not decision-grade
  2. command (log)            ← writes to reason_openai_log.jsonl
  3. command (pending queue)  ← writes to reason_openai_pending.jsonl
```

## Safety: stop_hook_active

The agent prompt uses `stop_hook_active` correctly:

> If stop_hook_active is true and the answer is already reasonably decision-grade, return {"ok": true} rather than demanding more polishing.

This prevents infinite polish loops when the verifier is called repeatedly.

## reason_openai_stop_agent_hook.py

The Python script version (for use with `type: "command"` if agent hooks are unavailable):

```python
#!/usr/bin/env python3
"""
reason_openai_stop_agent_hook.py — Agent-based Stop quality gate for /reason_openai.

This script is the command-wrapper fallback. The preferred installation uses
a "type: agent" Stop hook defined directly in settings.json.

Install (agent style, in settings.json):
  {
    "type": "agent",
    "prompt": "You are the final quality verifier for /reason_openai...",
    "timeout": 90
  }
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TRANSCRIPT_MARKER = "/reason_openai"

REQUIRED_SECTIONS = [
    "Route chosen",
    "Best current conclusion",
    "Why it wins",
    "Strongest challenge",
    "Biggest uncertainty",
    "Best next action",
]


def check_sections(content: str) -> list[str]:
    missing = []
    for section in REQUIRED_SECTIONS:
        pattern = rf"(?im)^(?:##\s*)?{section}\s*$"
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
    transcript_path = data.get("transcript_path") or ""

    if TRANSCRIPT_MARKER not in last_message and TRANSCRIPT_MARKER not in transcript_path:
        print(json.dumps({"ok": True}))
        return 0

    missing = check_sections(last_message)
    if missing:
        reason = "Strengthen the /reason_openai answer before stopping. Missing: " + ", ".join(missing)
        print(json.dumps({"ok": False, "reason": reason}))
        return 0

    print(json.dumps({"ok": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```