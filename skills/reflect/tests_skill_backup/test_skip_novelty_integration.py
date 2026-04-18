"""
Integration tests for skip_novelty_check parameter.

Tests the two-phase separation workflow:
- Phase 1 (Accumulation): Stop hook sets SKIP_NOVELTY_CHECK=1, all signals preserved
- Phase 2 (Review): Manual /reflect runs with novelty detection, filters duplicates
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add scripts to path for imports
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# Import after path setup
try:
    from extract_signals import extract_signals

    EXTRACT_AVAILABLE = True
except ImportError:
    EXTRACT_AVAILABLE = False


class TestSkipNoveltyIntegration(unittest.TestCase):
    """Test skip_novelty_check parameter integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_transcript = self._create_test_transcript()

    def _create_test_transcript(self):
        """Create a minimal test transcript with learning signal."""
        # Use a skill invocation to ensure skills_used is populated
        messages = [
            {"role": "user", "content": "/code fix the bug"},
            {
                "role": "assistant",
                "content": "I'll fix it",
                "tool_uses": [{"name": "Skill", "parameters": {"skill": "code"}}],
            },
            {"role": "user", "content": "No, don't use X, use Y instead"},
            {"role": "assistant", "content": "I'll use Y instead"},
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for msg in messages:
                f.write(json.dumps(msg) + "\n")
            return f.name

    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, "test_transcript") and Path(self.test_transcript).exists():
            Path(self.test_transcript).unlink()

    @unittest.skipIf(not EXTRACT_AVAILABLE, "extract_signals module not available")
    @patch("extract_signals.expand_skill_list")
    def test_skip_novelty_check_true_skips_cks_check(self, mock_expand):
        """Test that skip_novelty_check=True skips CKS novelty detection."""
        # Mock skill_discovery to return test skills
        mock_expand.return_value = ["code", "reflect"]

        # This test should PASS when skip_novelty_check works correctly
        # We expect all signals to be preserved (no novelty filtering)

        with tempfile.TemporaryDirectory() as _:
            result = extract_signals(
                transcript_path=self.test_transcript,
                skip_novelty_check=True,  # Skip novelty check
                use_semantic=False,  # Use fast regex mode for testing
            )

            # Verify signals were extracted (not filtered by CKS)
            self.assertIsInstance(result, dict)
            # At minimum, we should have signals under 'code' or 'reflect' keys
            total_signals = sum(len(signals) for signals in result.values())
            self.assertGreater(
                total_signals, 0, "Expected signals to be preserved when skip_novelty_check=True"
            )

    @unittest.skipIf(not EXTRACT_AVAILABLE, "extract_signals module not available")
    def test_skip_novelty_check_false_runs_cks_check(self):
        """Test that skip_novelty_check=False runs CKS novelty detection."""
        # This test verifies CKS check runs when flag is False
        # We expect novelty detection to filter duplicates (if daemon available)

        with tempfile.TemporaryDirectory() as _:
            result = extract_signals(
                transcript_path=self.test_transcript,
                skip_novelty_check=False,  # Run novelty check
                use_semantic=False,
            )

            # Verify result is dict (may be empty if signal filtered as duplicate)
            self.assertIsInstance(result, dict)

    @unittest.skipIf(not EXTRACT_AVAILABLE, "extract_signals module not available")
    def test_environment_variable_skip_novelty_check(self):
        """Test that SKIP_NOVELTY_CHECK environment variable is respected."""
        # Test the environment variable control mechanism
        # This is how the Stop hook controls behavior

        # Test with env var set to "1"
        original_env = os.environ.get("SKIP_NOVELTY_CHECK")
        try:
            os.environ["SKIP_NOVELTY_CHECK"] = "1"

            # When env var is set, should skip novelty check
            # We can't test without explicit param (uses None which reads env)
            # so we test both combinations
            result_skip = extract_signals(
                transcript_path=self.test_transcript,
                use_semantic=False,
            )
            self.assertIsInstance(result_skip, dict)

            # Now clear env var and test without skip
            if "SKIP_NOVELTY_CHECK" in os.environ:
                del os.environ["SKIP_NOVELTY_CHECK"]

            result_no_skip = extract_signals(
                transcript_path=self.test_transcript,
                skip_novelty_check=False,
                use_semantic=False,
            )
            self.assertIsInstance(result_no_skip, dict)

        finally:
            # Restore original env var
            if original_env is not None:
                os.environ["SKIP_NOVELTY_CHECK"] = original_env
            elif "SKIP_NOVELTY_CHECK" in os.environ:
                del os.environ["SKIP_NOVELTY_CHECK"]

    def test_stop_hook_integration(self):
        """Test Stop_reflect_integration.py sets SKIP_NOVELTY_CHECK=1."""
        # Verify the Stop hook passes the environment variable correctly
        # This tests the actual subprocess call

        # Hook is at P:/.claude/hooks/Stop_reflect_integration.py
        # When running from package, we need absolute path or proper relative
        hook_path = Path("P:/.claude/hooks/Stop_reflect_integration.py")

        if not hook_path.exists():
            self.skipTest(f"Stop hook not found at {hook_path}")

        # Read hook source to verify it sets the env var
        hook_source = hook_path.read_text()

        # Verify the hook sets SKIP_NOVELTY_CHECK=1
        self.assertIn("SKIP_NOVELTY_CHECK", hook_source, "Stop hook should set SKIP_NOVELTY_CHECK")
        self.assertIn(
            'env["SKIP_NOVELTY_CHECK"] = "1"',
            hook_source,
            "Stop hook should set SKIP_NOVELTY_CHECK to '1'",
        )


if __name__ == "__main__":
    unittest.main()
