#!/usr/bin/env python3
"""Stage E3: CSS/JS Assembler — concatenates all CSS and JS files in order.
Writes e3-output.json.

Reads: e2-output.json + template CSS/JS files
Output: e3-output.json (with css_block and js_block strings)
Note: PALETTES is already embedded in diagram-scripts.js — no injection needed here."""
import json, sys
from pathlib import Path

BASE  = Path("P:/packages/cc-skills-meta/skills/skill-to-page")
TPL   = BASE / "templates"
E2_OUT = BASE / "e2-output.json"

CSS_ORDER = ["shared-css.css", "toc-css.css", "section-css.css", "diagram-css.css"]
JS_ORDER  = ["shared-scripts.js", "diagram-scripts.js"]

def load_json(p):
    return json.loads(p.read_text(encoding="utf-8"))

def read(name):
    return (TPL / name).read_text(encoding="utf-8")

def main():
    e2 = load_json(E2_OUT)
    if e2.get("status") != "pass":
        print("E2 must pass before E3 can run")
        sys.exit(1)

    plan = load_json(BASE / "artifact-plan.json")

    errors = []

    # Concatenate CSS
    css_parts = []
    for name in CSS_ORDER:
        try:
            css_parts.append(read(name).strip())
        except Exception as ex:
            errors.append(f"missing CSS file: {name} ({ex})")
    css_block = "\n\n".join(css_parts)

    # Concatenate JS
    js_parts = []
    for name in JS_ORDER:
        try:
            js_parts.append(read(name).strip())
        except Exception as ex:
            errors.append(f"missing JS file: {name} ({ex})")
    js_block = "\n\n".join(js_parts)

    # NOTE: diagram-scripts.js already has its own PALETTES object with the correct
    # camelCase strokeWidth keys for the selected palette. Do NOT inject another
    # PALETTES object here — it would create a duplicate const declaration and
    # cause a SyntaxError at module load time, breaking all JS.
    # The PALETTES in diagram-scripts.js is the canonical one.

    output = {
        "stage": "E3",
        "status": "fail" if errors else "pass",
        "css_parts": CSS_ORDER,
        "js_parts": JS_ORDER,
        "palette_note": "PALETTES already in diagram-scripts.js — not injected",
        "css_size": len(css_block),
        "js_size": len(js_block),
        "errors": errors,
    }

    out_path = BASE / "e3-output.json"
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

    # Write assembled CSS/JS to companion files
    (BASE / "e3_css_block.css").write_text(css_block, encoding="utf-8")
    (BASE / "e3_js_block.js").write_text(js_block, encoding="utf-8")

    print(f"E3: {'PASS' if not errors else 'FAIL'} — CSS {len(css_block)} chars, JS {len(js_block)} chars")
    if errors:
        for e in errors: print(f"  ERROR: {e}")
        sys.exit(1)
    print(f"E3 written to {out_path}")

if __name__ == "__main__":
    main()