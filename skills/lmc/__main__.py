#!/usr/bin/env python3
"""
LMC Skill Entry Point

Lossy Minimal Compaction - Aggressive context optimization for
hard token limits.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import skill execution
from skill import main

if __name__ == "__main__":
    main()
