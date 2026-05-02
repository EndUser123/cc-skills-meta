"""Stop hook: epistemic contract enforcement."""

import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).parent
LIB_DIR = HOOKS_DIR / "__lib"
sys.path.insert(0, str(LIB_DIR))

try:
    from epistemic_validator import run_all_checks, EpistemicConfig
except ImportError:
    print("ERROR: Cannot import epistemic_validator", file=sys.stderr)
    sys.exit(0)  # Non-blocking


def main() -> None:
    # Read inputs from stdin (Claude Code hook protocol)
    import json
    data = json.load(sys.stdin)

    user_input = data.get("user_input", "")
    response = data.get("response", "")
    tool_name = data.get("tool_name", "")

    # Skip non-Stop hooks
    if tool_name and tool_name != "Stop":
        sys.exit(0)

    config = EpistemicConfig()
    issues = run_all_checks(user_input, response, config)

    if issues:
        for issue in issues:
            print(f"⚠️ EPISTEMIC: {issue.message}", file=sys.stderr)
        if any(i.type == "missing_direct_answer" and config.treat_missing_direct_answer_as == "error" for i in issues):
            sys.exit(2)  # Block
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
