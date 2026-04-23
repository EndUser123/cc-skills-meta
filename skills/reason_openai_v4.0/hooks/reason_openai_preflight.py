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
