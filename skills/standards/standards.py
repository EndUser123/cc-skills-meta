#!/usr/bin/env python
"""
standards.py - CSF Standards Reference

Executable wrapper for the /standards skill.
Returns proper dict format for StopRouter.
"""

import json
import sys
from pathlib import Path

# Read and return the standards content
def main():
    """Return standards as dict format."""
    skill_file = Path(__file__).parent / "SKILL.md"

    result = {
        "statusLine": "📋 CSF Standards loaded",
        "internalPrompt": skill_file.read_text(encoding='utf-8') if skill_file.exists() else "# Standards not found"
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
