---
description: SubagentStop agent hook for red_team, implementation_realist, and decision_editor quality gates.
allowed-tools: Bash(python:*)
---

# reason_openai SubagentStop Hook

A `SubagentStop` agent hook that verifies output quality for the three custom subagents before they stop.

## Subagents Guarded

| Subagent | Verifies |
|----------|----------|
| `red_team` | Sharp, concrete, adversarial objections — not generic caution |
| `implementation_realist` | Execution reality, not architectural theater |
| `decision_editor` | Compression, choice, and clarity — not sprawling indecision |

## Install

Add to `~/.claude/settings.json` alongside the existing Stop hooks:

```json
{
  "hooks": {
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "agent",
            "prompt": "You are the final quality verifier for custom subagents. The hook input JSON is: $ARGUMENTS\n\nUse `last_assistant_message` as the primary artifact.\nIf `stop_hook_active` is true and the output is already reasonably usable, return exactly JSON: {\"ok\": true} rather than demanding more polishing.\n\nDetermine which subagent just completed. If it is not `red_team`, `implementation_realist`, or `decision_editor`, return exactly JSON: {\"ok\": true}.\n\nFor `red_team`, require: Main objection, Failure modes, Hidden assumption, What would change your mind, Severity. The content must be concrete and adversarial, not generic caution.\n\nFor `implementation_realist`, require: Practical verdict, Main implementation risk, Operational burden, Simplest viable version, Recommendation. The content must be execution-focused and operationally realistic.\n\nFor `decision_editor`, require: Best current conclusion, Why it wins, Strongest challenge, Best next action, Ignore. The content must compress and choose rather than preserving indecision.\n\nIf missing or weak, return exactly JSON: {\"ok\": false, \"reason\": \"Strengthen the subagent output before stopping. <very short specific correction>.\"}\nIf good enough, return exactly JSON: {\"ok\": true}.",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

## Quality Standards Per Subagent

### red_team
- **Main objection** — one sharp, concrete objection, not vague discomfort
- **Failure modes** — 2–5 specific failure scenarios, not generic warnings
- **Hidden assumption** — names the assumption doing the most work
- **What would change your mind** — specific falsifying evidence or constraint
- **Severity** — Low / Medium / High with justification
- **Anti-generic rule**: "could fail" without mechanism = fail. "The dependency could timeout and cascade" = pass.

### implementation_realist
- **Practical verdict** — can it actually be executed well?
- **Main implementation risk** — single biggest real-world risk with mechanism
- **Operational burden** — ongoing cost or complexity added, not just one-time setup
- **Simplest viable version** — preserves most value with less risk
- **Recommendation** — Ship / Revise / Avoid
- **Anti-theater rule**: abstract design praise without execution detail = fail.

### decision_editor
- **Best current conclusion** — one clear recommendation, not hedged
- **Why it wins** — 2–5 bullets, not paragraphs
- **Strongest challenge** — one real objection, not a list
- **Best next action** — concrete, not vague
- **Ignore** — what not to spend time on, if useful
- **Anti-clutter rule**: preserving more than 3 options = fail. Vague hedging = fail.

## Anti-loop Safeguard

```
If stop_hook_active is true and the output is already reasonably usable, return {"ok": true}
```

This prevents infinite polish loops in subagents that are already good enough.

## reason_openai_subagent_stop_hook.py

Fallback Python script (for command-based installation if agent hooks are unavailable):

```python
#!/usr/bin/env python3
"""
reason_openai_subagent_stop_hook.py — SubagentStop quality gate for subagents.

Install as command hook fallback only if agent hooks are unavailable.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

AGENT_MARKERS = ["red_team", "implementation_realist", "decision_editor"]

RED_TEAM_SECTIONS = ["Main objection", "Failure modes", "Hidden assumption", "What would change your mind", "Severity"]
IMPL_SECTIONS = ["Practical verdict", "Main implementation risk", "Operational burden", "Simplest viable version", "Recommendation"]
DECISION_SECTIONS = ["Best current conclusion", "Why it wins", "Strongest challenge", "Best next action", "Ignore"]

SECTION_MAP = {
    "red_team": RED_TEAM_SECTIONS,
    "implementation_realist": IMPL_SECTIONS,
    "decision_editor": DECISION_SECTIONS,
}


def detect_agent(content: str) -> str | None:
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
```