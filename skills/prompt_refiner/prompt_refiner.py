#!/usr/bin/env python
"""
prompt_refiner.py - Prompt Refiner Reference

Executable wrapper for the /prompt_refiner skill.
Returns proper dict format for StopRouter.
"""

import json
import sys
from pathlib import Path

def main():
    """Return prompt refiner as dict format."""
    skill_file = Path(__file__).parent / "SKILL.md"

    result = {
        "statusLine": "📋 Prompt Refiner loaded",
        "internalPrompt": skill_file.read_text(encoding='utf-8') if skill_file.exists() else "# Prompt Refiner not found"
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
