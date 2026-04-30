#!/usr/bin/env python3
"""Stage E1: Template Loader — verifies all template files exist and required
DOM elements are present. Writes e1-output.json.

Input:  artifact-plan.json (reads template_version)
Output: e1-output.json
Gate:   all templates exist AND all required DOM elements present
"""
import json, sys
from pathlib import Path

BASE = Path("P:/packages/cc-skills-meta/skills/skill-to-page")
TPL  = BASE / "templates"
ARTIFACT_PLAN = BASE / "artifact-plan.json"

REQUIRED_TEMPLATES = [
    "base-shell.html",
    "toc.html",
    "shared-css.css",
    "toc-css.css",
    "section-css.css",
    "diagram-css.css",
    "shared-scripts.js",
    "diagram-scripts.js",
    "mermaid-palettes.json",
    "hero.html",
    "facts.html",
    "search-ui.html",
    "mermaid-panel.html",
    "steps-accordion.html",
    "route-outs.html",
    "terminals.html",
    "artifacts.html",
    "proof-summary.html",
]

# DOM elements that MUST be present in the template that emits them
REQUIRED_ELEMENTS = {
    "toc_toggle":      '<button id="tocToggle"',
    "toc_element":      '<nav id="toc" class="toc"',
    "mermaid_source":  'id="mermaidSource"',
    "resize_handle":    'id="diagramResizeHandle"',
    "theme_toggle":     'id="themeToggle"',
    "search_input":     'id="searchInput"',
    "diagram_viewport": 'id="diagramViewport"',
    "diagram_stage":    'id="diagramStage"',
    "zoom_controls":    'id="zoomIn"',
}

def read_template(name):
    path = TPL / name
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")

def main():
    errors = []
    templates_loaded = {}
    structure_elements = {}

    # Check template files exist
    for name in REQUIRED_TEMPLATES:
        content = read_template(name)
        if content is None:
            errors.append(f"missing template: {name}")
        else:
            templates_loaded[name] = f"{len(content)} chars"

    # Check required DOM elements
    for elem_id, pattern in REQUIRED_ELEMENTS.items():
        found = False
        for name, content in [(n, read_template(n)) for n in REQUIRED_TEMPLATES]:
            if content and pattern in content:
                found = True
                structure_elements[elem_id] = name
                break
        if not found:
            errors.append(f"missing element: {elem_id} (pattern: {pattern})")

    output = {
        "stage": "E1",
        "status": "pass" if not errors else "fail",
        "template_version": "v1",
        "templates_loaded": templates_loaded,
        "structure_elements": structure_elements,
        "errors": errors,
    }

    out_path = BASE / "e1-output.json"
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"E1: {'PASS' if not errors else 'FAIL'} — {len(templates_loaded)}/{len(REQUIRED_TEMPLATES)} templates, {len(structure_elements)}/{len(REQUIRED_ELEMENTS)} elements")
    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
        sys.exit(1)
    else:
        print(f"E1 written to {out_path}")

if __name__ == "__main__":
    main()