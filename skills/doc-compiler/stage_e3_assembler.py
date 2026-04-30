#!/usr/bin/env python3
"""Stage E3: CSS/JS Assembler for doc-compiler.

Concatenates all CSS and JS files in order,
inlines the selected Mermaid palette.
Output: e3-output.json (with css_block and js_block strings)
"""
import json, sys
from pathlib import Path

BASE  = Path("P:/packages/cc-skills-meta/skills/doc-compiler")
TPL   = BASE / "templates"
E2_OUT = BASE / "e2-output.json"
PALETTES_FILE = TPL / "mermaid-palettes.json"

CSS_ORDER = ["shared-css.css", "toc-css.css", "section-css.css", "diagram-css.css"]
JS_ORDER  = ["shared-scripts.js", "diagram-scripts.js"]


def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def read(name: str) -> str:
    return (TPL / name).read_text(encoding="utf-8")


def main() -> None:
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

    # Inline selected palette into JS block
    palette_name = plan.get("ui_config", {}).get("palette", "tailwind-modern")
    try:
        palettes = json.loads(read("mermaid-palettes.json"))
    except Exception as ex:
        errors.append(f"failed to load palettes: {ex}")
        palettes = {}

    if palette_name not in palettes:
        errors.append(f"palette '{palette_name}' not in mermaid-palettes.json")
    else:
        palette_data = palettes[palette_name]
        palettes_json = json.dumps(palette_data, indent=2)
        palettes_inject = f"const PALETTES = {palettes_json};"
        js_block = palettes_inject + "\n\n" + js_block

    output = {
        "stage": "E3",
        "status": "fail" if errors else "pass",
        "css_parts": CSS_ORDER,
        "js_parts": JS_ORDER,
        "palette_inlined": palette_name if not errors else None,
        "css_size": len(css_block),
        "js_size": len(js_block),
        "errors": errors,
    }

    out_path = BASE / "e3-output.json"
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

    (BASE / "e3_css_block.css").write_text(css_block, encoding="utf-8")
    (BASE / "e3_js_block.js").write_text(js_block, encoding="utf-8")

    print(f"E3: {'PASS' if not errors else 'FAIL'} — CSS {len(css_block)} chars, JS {len(js_block)} chars")
    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
        sys.exit(1)
    print(f"E3 written to {out_path}")


if __name__ == "__main__":
    main()
