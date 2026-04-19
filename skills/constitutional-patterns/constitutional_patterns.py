#!/usr/bin/env python3
"""
constitutional_patterns.py - Constitutional Patterns Reference

Executable wrapper for the /constitutional-patterns skill.
Returns proper dict format for StopRouter.
"""

import json
import sys
from pathlib import Path

def main():
    """Return constitutional patterns as dict format."""
    skill_file = Path(__file__).parent / "SKILL.md"

    result = {
        "statusLine": "📋 Constitutional Patterns loaded",
        "internalPrompt": skill_file.read_text(encoding='utf-8') if skill_file.exists() else "# Constitutional Patterns not found"
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
