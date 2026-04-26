#!/usr/bin/env python
"""Integration tests for GTO v3 self-verifying infrastructure.

Tests the complete flow: GTO run → artifacts → assertions → hook block/pass
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


class TestGTOVerificationFlow:
    """Integration tests for complete GTO verification workflow."""

    def test_json_error_handling_in_failure_capture(self, tmp_path: Path) -> None:
        """Test failure capture hook handles malformed JSON gracefully.

        Scenario:
        1. Run failure capture hook with invalid JSON stdin
        2. Verify hook doesn't crash
        3. Verify valid JSON output returned
        """
        failure_capture = Path(__file__).parent.parent / "hooks" / "gto_failure_capture.py"

        # Invalid JSON input
        invalid_json = "{ this is not valid json"

        result = subprocess.run(
            [sys.executable, str(failure_capture)],
            input=invalid_json,
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Assertions: Should return valid JSON even with invalid input
        assert result.returncode == 0
        # Output should be valid JSON
        try:
            output = json.loads(result.stdout)
            assert "additionalContext" in output
        except json.JSONDecodeError:
            pytest.fail("Failure capture hook did not return valid JSON")
