#!/usr/bin/env python3
"""Stage B: Artifact Plan Builder for doc-compiler.

Reads source-model.json from Stage A and designs the page structure.
Emits artifact-plan.json.
"""
import json, sys
from pathlib import Path

BASE = Path("P:/packages/cc-skills-meta/skills/doc-compiler")
SOURCE = BASE / "source-model.json"
OUT    = BASE / "artifact-plan.json"

PALETTE_DEFAULT = "tailwind-modern"
TOC_WIDTH = "18rem"
TOC_BREAKPOINT = 960
DIAGRAM_HEIGHT_INIT = 480
DIAGRAM_HEIGHT_MIN = 200
DIAGRAM_HEIGHT_MAX = 800


def build_artifact_plan(model: dict) -> dict:
    """Build artifact-plan.json from source model."""
    steps = model.get("steps", [])
    route_outs = model.get("route_outs", [])
    terminal_states = model.get("terminal_states", [])
    artifacts = model.get("artifacts", [])

    step_ids = [s.get("id", f"step-{i}") for i, s in enumerate(steps, 1)]

    return {
        "template": "default-docs-v1",
        "template_version": "v1",
        "page_structure": {
            "sections": [
                {"id": "overview", "type": "hero", "title": "Overview"},
                {"id": "facts", "type": "quick-facts", "items": []},
                {"id": "diagram", "type": "mermaid"},
                {"id": "steps", "type": "accordion", "items": step_ids},
                {"id": "route-outs", "type": "route-out-list"},
                {"id": "terminals", "type": "terminal-list"},
                {"id": "artifacts", "type": "artifact-cards"},
                {"id": "proof", "type": "proof-metadata"}
            ]
        },
        "ui_config": {
            "palette": PALETTE_DEFAULT,
            "toc_width": TOC_WIDTH,
            "toc_breakpoint": TOC_BREAKPOINT,
            "diagram_height_initial": DIAGRAM_HEIGHT_INIT,
            "diagram_height_min": DIAGRAM_HEIGHT_MIN,
            "diagram_height_max": DIAGRAM_HEIGHT_MAX
        },
        "mermaid_source": "",
        "mermaid_config": {"curve": "basis", "nodeSpacing": 40, "rankSpacing": 50},
        "toc_config": {"width": TOC_WIDTH, "breakpoint": TOC_BREAKPOINT},
        "css_contract": {
            "toggle_position": "fixed",
            "toggle_left": "0",
            "toc_transition": "left",
            "no_transform_on_desktop": True,
            "toggle_outside_nav": True,
            "mobile_toggle_display": "flex"
        },
        "content_bindings": {
            "name": model.get("name", ""),
            "version": model.get("version", ""),
            "description": model.get("description", ""),
            "steps": steps,
            "route_outs": route_outs,
            "terminal_states": terminal_states,
            "artifacts": artifacts
        }
    }


def main() -> None:
    if not SOURCE.exists():
        print(f"ERROR: {SOURCE} not found. Run Stage A first.", file=sys.stderr)
        sys.exit(1)

    try:
        model = json.loads(SOURCE.read_text(encoding="utf-8"))
    except Exception as ex:
        print(f"ERROR: failed to read {SOURCE}: {ex}", file=sys.stderr)
        sys.exit(1)

    gaps = model.get("gaps", [])
    ambiguities = model.get("ambiguities", [])

    plan = build_artifact_plan(model)

    # Gate: ambiguities must be recorded if present
    if gaps or ambiguities:
        plan["gaps"] = gaps
        plan["ambiguities"] = ambiguities
        if ambiguities:
            print(f"WARNING: {len(ambiguities)} ambiguities recorded")

    OUT.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    steps_count = len(plan["content_bindings"]["steps"])
    print(f"Stage B: PASS — plan built with {steps_count} steps")
    print(f"Written: {OUT}")
    sys.exit(0)


if __name__ == "__main__":
    main()
