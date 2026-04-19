"""
Test CLI commands for the Master Skill Orchestrator.

This script validates all CLI commands work correctly.
Run with: python test_cli.py
"""

import subprocess
import sys
import json
import os
from pathlib import Path


class CLITester:
    """Test CLI commands."""

    def __init__(self):
        self.cli_path = Path(__file__).parent / "cli.py"
        self.passed = 0
        self.failed = 0
        self.errors = []

    def run_command(self, args, expect_success=True, check_json=False):
        """Run a CLI command and check results."""
        cmd = [sys.executable, str(self.cli_path)] + args

        # Set environment to disable Git Bash path conversion
        env = os.environ.copy()
        env['MSYS_NO_PATHCONV'] = '1'

        # Prevent blue console flash on Windows
        creation_flags = 0x08000000 if sys.platform == 'win32' else 0

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
                creationflags=creation_flags
            )

            # Check exit code
            if expect_success and result.returncode != 0:
                self.errors.append(f"Command failed: {' '.join(args)}")
                self.failed += 1
                return False

            if not expect_success and result.returncode == 0:
                self.errors.append(f"Command should have failed: {' '.join(args)}")
                self.failed += 1
                return False

            # Check JSON output if requested
            if check_json:
                try:
                    json.loads(result.stdout)
                except json.JSONDecodeError as e:
                    self.errors.append(f"Invalid JSON output: {' '.join(args)} - {e}")
                    self.failed += 1
                    return False

            self.passed += 1
            return True

        except subprocess.TimeoutExpired:
            self.errors.append(f"Command timed out: {' '.join(args)}")
            self.failed += 1
            return False
        except Exception as e:
            self.errors.append(f"Exception running command: {' '.join(args)} - {e}")
            self.failed += 1
            return False

    def test_help(self):
        """Test help command."""
        print("Testing: --help")
        return self.run_command(['--help'])

    def test_version(self):
        """Test version command."""
        print("Testing: --version")
        return self.run_command(['--version'])

    def test_suggest(self):
        """Test suggest command."""
        print("Testing: suggest /nse")
        return self.run_command(['suggest', '/nse'])

    def test_info(self):
        """Test info command."""
        print("Testing: info /nse")
        return self.run_command(['info', '/nse'])

    def test_stats(self):
        """Test stats command."""
        print("Testing: stats")
        return self.run_command(['stats'])

    def test_stats_json(self):
        """Test stats command with JSON output."""
        print("Testing: --json stats")
        return self.run_command(['--json', 'stats'], check_json=True)

    def test_history(self):
        """Test history command."""
        print("Testing: history --limit 3")
        return self.run_command(['history', '--limit', '3'])

    def test_graph(self):
        """Test graph command."""
        print("Testing: graph")
        return self.run_command(['graph'])

    def test_workflow(self):
        """Test workflow command."""
        print("Testing: workflow /nse --depth 2")
        return self.run_command(['workflow', '/nse', '--depth', '2'])

    def test_invoke(self):
        """Test invoke command."""
        print("Testing: invoke /nse")
        return self.run_command(['invoke', '/nse'])

    def test_validate_valid(self):
        """Test validate command with valid workflow."""
        print("Testing: validate '/nse,/r' (should succeed)")
        return self.run_command(['validate', '/nse,/r'], expect_success=True)

    def test_invalid_skill(self):
        """Test with invalid skill name."""
        print("Testing: info /nonexistent-skill-xyz")
        return self.run_command(['info', '/nonexistent-skill-xyz'], expect_success=False)

    def run_all_tests(self):
        """Run all tests."""
        print("=" * 60)
        print("Master Skill Orchestrator CLI Test Suite")
        print("=" * 60)
        print()

        tests = [
            self.test_help,
            self.test_version,
            self.test_suggest,
            self.test_info,
            self.test_stats,
            self.test_stats_json,
            self.test_history,
            self.test_graph,
            self.test_workflow,
            self.test_invoke,
            self.test_validate_valid,
            self.test_invalid_skill,
        ]

        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"  ❌ Test failed with exception: {e}")
                self.failed += 1
                self.errors.append(f"{test.__name__}: {e}")

        # Print summary
        print()
        print("=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Total:  {self.passed + self.failed}")
        print()

        if self.errors:
            print("Errors:")
            for error in self.errors:
                print(f"  ❌ {error}")
            print()

        return self.failed == 0


def main():
    """Run tests."""
    tester = CLITester()
    success = tester.run_all_tests()

    if success:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
