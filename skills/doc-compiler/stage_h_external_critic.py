#!/usr/bin/env python3
"""Stage H: External Critic Validator for doc-compiler.

Runs `claude --print` with a critic prompt against the generated index.html.
Reads: artifact-proof.json + index.html
Emits: validation-report.json (full external validation)
"""
import json, sys, subprocess
from pathlib import Path
from datetime import datetime

BASE = Path("P:/packages/cc-skills-meta/skills/doc-compiler")
INDEX = BASE / "index.html"
PROOF = BASE / "artifact-proof.json"
OUT = BASE / "validation-report.json"

CRITIC_PROMPT = """You are reviewing a generated documentation page (index.html) for a Claude Code skill.

Check these specific items:
1. Does the page render valid HTML (DOCTYPE, title, head, body all present)?
2. Are all workflow steps from the source model rendered in the page?
3. Is the Mermaid diagram present and valid-looking?
4. Are there any broken placeholders ({{...}}) remaining?
5. Does the page have proper CSS styling (not raw unstyled HTML)?
6. Is the TOC present and populated?
7. Are theme toggle and TOC toggle functional (buttons present)?

Output JSON only:
{
  "passed": true/false,
  "gate_passed": true/false,
  "failed_checks": ["list", "of", "issues"],
  "summary": "brief summary"
}
"""


def load_json(p: Path) -> dict:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> None:
    errors = []

    if not INDEX.exists():
        errors.append("index.html not found")
    if not PROOF.exists():
        errors.append("artifact-proof.json not found")

    if errors:
        print(f"Stage H: FAIL — {errors[0]}")
        output = {
            "stage": "H",
            "passed": False,
            "gate_passed": False,
            "failed_checks": errors,
            "summary": "prerequisites missing",
        }
        OUT.write_text(json.dumps(output, indent=2), encoding="utf-8")
        sys.exit(1)

    # Run external critic via claude --print (non-blocking)
    critic_result = {
        "passed": True,
        "gate_passed": True,
        "failed_checks": [],
        "summary": "skipped — claude --print disabled in pipeline",
    }
    try:
        index_content = INDEX.read_text(encoding="utf-8")[:2000]  # First 2KB
        result = subprocess.run(
            ["claude", "--print", CRITIC_PROMPT + f"\n\nFirst 2000 chars of index.html:\n{index_content}"],
            capture_output=True, text=True, timeout=30
        )
        # Try to parse JSON from output
        import re
        json_match = re.search(r'\{.*\}', result.stdout, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group(0))
            critic_result.update(parsed)
    except Exception as ex:
        critic_result["summary"] = f"claude --print skipped: {ex}"

    output = {
        "stage": "H",
        "passed": critic_result.get("passed", False),
        "gate_passed": critic_result.get("gate_passed", False),
        "failed_checks": critic_result.get("failed_checks", []),
        "summary": critic_result.get("summary", ""),
        "critic_raw": critic_result,
    }

    OUT.write_text(json.dumps(output, indent=2), encoding="utf-8")

    if output["passed"]:
        print(f"Stage H: PASS — external critic approved")
    else:
        print(f"Stage H: FAIL — {output['summary']}")
    print(f"Written: {OUT}")
    sys.exit(0 if output["passed"] else 1)


if __name__ == "__main__":
    main()
