#!/usr/bin/env python
"""GTO Verification Stop Hook - Platform-aware wrapper with scope guard.

This script:
1. Checks if GTO was actually used (scope guard)
2. Detects the platform and runs the appropriate verification script
3. Returns appropriate exit codes

Exit codes:
- 0: Verification passed (or skipped - GTO not used)
- 2: Verification failed, must retry
"""

import json
import os
import sys
from pathlib import Path


# Add hooks to path for shared utilities
# Search upward for hooks directory instead of hardcoded parent levels
def _find_hooks_dir(start_path: Path) -> Path:
    """Find hooks directory by searching upward from start_path."""
    current = start_path.resolve()
    for parent in [current, *current.parents]:
        hooks_dir = parent / "hooks"
        if hooks_dir.exists() and (hooks_dir / "__lib" / "hook_base.py").exists():
            return hooks_dir
    raise FileNotFoundError("Could not find hooks directory with __lib/hook_base.py")


def _safe_imports() -> tuple:
    """Import hook utilities with graceful fallback.

    Returns:
        Tuple of (get_terminal_id, run_platform_hook, scope_guard_check) or None if unavailable.

    On failure, prints structured diagnostic and returns None.
    """
    try:
        sys.path.insert(0, str(_find_hooks_dir(Path(__file__))))
        from __lib.hook_base import get_terminal_id
        from __lib.hook_platform import run_platform_hook, scope_guard_check
        return (get_terminal_id, run_platform_hook, scope_guard_check)
    except (ImportError, AttributeError) as e:
        # Skill-based hooks: catch import errors and return structured diagnostic
        # instead of raw stderr which Claude Code renders as "hook error"
        print(
            json.dumps({
                "decision": "warn",
                "systemMessage": (
                    f"hook_platform unavailable ({type(e).__name__}) — "
                    "GTO verification skipped. Details logged to diagnostics."
                )
            })
        )
        return None
    except Exception as e:
        print(
            json.dumps({
                "decision": "warn",
                "systemMessage": (
                    f"Unexpected error during import ({type(e).__name__}) — "
                    "GTO verification skipped."
                )
            })
        )
        return None


_get_terminal_id, _run_platform_hook, _scope_guard_check = None, None, None

# Attempt imports at module load time
_import_result = _safe_imports()
if _import_result:
    _get_terminal_id, _run_platform_hook, _scope_guard_check = _import_result


def main() -> int:
    """Main entry point."""
    # Get terminal ID using centralized function with fallbacks
    # For skill-based hooks, CLAUDE_TERMINAL_ID is not available
    # Use get_terminal_id() which derives from console/PID+timestamp
    terminal_id = _get_terminal_id() if _get_terminal_id else None
    if not terminal_id:
        print(
            '{"decision": "block", "reason": "Unable to determine terminal ID for multi-terminal isolation."}'
        )
        return 2

    project_root = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
    if not project_root.exists():
        print(json.dumps({"decision": "block", "reason": "CLAUDE_PROJECT_DIR points to non-existent path"}))
        return 2

    # Scope guard: Check if GTO was actually used
    if _scope_guard_check is None:
        # Hook utilities unavailable - skip verification gracefully
        print("GTO scope guard: skipped (hook_platform unavailable)")
        return 0

    should_skip, reason = _scope_guard_check(project_root, "gto-state-{terminal_id}", terminal_id)

    if should_skip:
        print(f"GTO scope guard: {reason}")
        return 0  # Skip (pass) - GTO was not used

    # Run platform-specific verification hook
    script_dir = Path(__file__).parent

    if _run_platform_hook is None:
        print("GTO verification: skipped (hook_platform unavailable)")
        return 0

    try:
        exit_code, stdout, stderr = _run_platform_hook(
            script_dir=script_dir,
            script_name="gto_verify",
            env={
                "TERMINAL_ID": terminal_id,
                "CLAUDE_PROJECT_DIR": str(project_root),
            },
            timeout=30,
        )

        # Output the verification result
        if stdout:
            print(stdout, end="")
        if stderr:
            print(stderr, file=sys.stderr)

        return exit_code

    except FileNotFoundError as e:
        print(json.dumps({"decision": "block", "reason": f"GTO verification script not found: {e}"}))
        return 2  # Block if script not found


if __name__ == "__main__":
    sys.exit(main())
