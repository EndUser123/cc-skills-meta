#!/usr/bin/env python
"""
solo_dev_authority.py - Solo Dev Authority Constraints

Executable wrapper for the /solo-dev-authority skill.
Returns proper dict format for StopRouter.
"""

import json
import sys
from pathlib import Path

# Read and return the solo-dev authority content
def main():
    """Return solo-dev authority as dict format."""
    skill_file = Path(__file__).parent / "SKILL.md"

    result = {
        "statusLine": "📋 Solo Dev Authority loaded",
        "internalPrompt": skill_file.read_text(encoding='utf-8') if skill_file.exists() else "# Solo Dev Authority not found"
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
