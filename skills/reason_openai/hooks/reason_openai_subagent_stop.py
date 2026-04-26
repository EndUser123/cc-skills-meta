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