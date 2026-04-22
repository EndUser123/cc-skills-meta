#!/usr/bin/env python
"""
constraints.py - CSF Constraints Reference

Executable wrapper for the /constraints skill.
Returns proper dict format for StopRouter.
"""

import json
import sys
from pathlib import Path

# Read and return the constraints content
def main():
    """Return constraints as dict format."""
    skill_file = Path(__file__).parent / "SKILL.md"

    result = {
        "statusLine": "📋 CSF Constraints loaded",
        "internalPrompt": skill_file.read_text(encoding='utf-8') if skill_file.exists() else "# Constraints not found"
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
