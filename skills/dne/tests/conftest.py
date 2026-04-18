"""
Pytest configuration for /dne skill tests.

This file ensures that the tests can import from the scripts package.
"""

import sys
from pathlib import Path

# Add the parent directory to sys.path so tests can import from scripts
# This allows tests to use: from scripts.risk_calculator import ...
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))
