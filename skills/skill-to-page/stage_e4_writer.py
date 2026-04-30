#!/usr/bin/env python3
"""Stage E4: HTML Writer — assembles the final index.html from all E1-E3 outputs.

Reads: e1-output.json, e2-output.json, e3-output.json, e2_filled_*.html, e3_css_block.css, e3_js_block.js
Output: index.html + e4-output.json
Behavior: Takes assembled CSS + JS + filled templates, concatenates into a valid HTML file.
"""
import json, sys
from pathlib import Path

BASE   = Path("P:/packages/cc-skills-meta/skills/skill-to-page")
TPL    = BASE / "templates"

SECTION_ORDER = [
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

def read(name):
    return (BASE / name).read_text(encoding="utf-8")

def main():
    # Gate: E1, E2, E3 must all pass
    for stage, path in [("E1", BASE/"e1-output.json"), ("E2", BASE/"e2-output.json"), ("E3", BASE/"e3-output.json")]:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("status") != "pass":
            print(f"{stage} must pass before E4 can run")
            sys.exit(1)

    # Load assembled CSS and JS
    css_block = read("e3_css_block.css")
    js_block  = read("e3_js_block.js")

    # Load base-shell — extract proper <head> lines
    base = read("templates/base-shell.html")
    base_lines = base.split("\n")
    # base-shell.html lines 1-9 = DOCTYPE through last link; add clean </head>
    head_lines = base_lines[:9]
    head_lines.append("  </head>")

    # Load TOC
    toc_html = read("templates/toc.html")

    # Load filled section templates
    filled_sections = {}
    for name in SECTION_ORDER:
        try:
            filled_sections[name] = read(f"e2_filled_{name}")
        except FileNotFoundError:
            # Fall back to raw template if E2 didn't produce a filled version
            filled_sections[name] = read(f"templates/{name}")

    # Assemble HTML
    lines = []

    # Head
    for hl in head_lines:
        lines.append(hl)

    # Style block
    lines.append("  <style>")
    for cl in css_block.split("\n"):
        lines.append("    " + cl)
    lines.append("  </style>")

    # Body open
    lines.append("<body>")
    lines.append('<button id="tocToggle" aria-label="Toggle table of contents" title="Toggle TOC" aria-expanded="true">☰</button>')
    lines.append('<div class="page-shell">')

    # TOC sidebar
    for tl in toc_html.strip().split("\n"):
        lines.append("  " + tl)

    # Main content
    lines.append('  <div class="main-content">')
    for name in SECTION_ORDER:
        content = filled_sections.get(name, "")
        for bl in content.strip().split("\n"):
            lines.append("    " + bl)
    lines.append("  </div><!-- .main-content -->")
    lines.append("</div><!-- .page-shell -->")

    # Collect all import lines from the js_block and emit them first
    # ES modules require imports at the top; remaining code follows
    # Collect all import lines from the js_block and emit them first
    import_lines = [line for line in js_block.split("\n") if line.strip().startswith("import ")]
    other_lines = [line for line in js_block.split("\n") if not line.strip().startswith("import ")]

    lines.append('<script type="module">')
    # ES modules require all import declarations at the top
    for il in import_lines:
        lines.append("  " + il)
    for jl in other_lines:
        lines.append("  " + jl)
    lines.append('</script>')

    lines.append("</body>")
    lines.append("</html>")

    html = "\n".join(lines)
    out_path = BASE / "index.html"
    out_path.write_text(html, encoding="utf-8")

    # Verify key DOM elements are present
    checks = {
        "doctype":          html.startswith("<!DOCTYPE html>"),
        "toc_toggle":        'id="tocToggle"' in html,
        "toc_element":      'id="toc"' in html and 'class="toc"' in html,
        "mermaid_source":   'id="mermaidSource"' in html,
        "resize_handle":     'id="diagramResizeHandle"' in html,
        "theme_toggle":      'id="themeToggle"' in html,
        "search_input":      'id="searchInput"' in html,
        "diagram_viewport":  'id="diagramViewport"' in html,
        "diagram_stage":     'id="diagramStage"' in html,
        "zoom_controls":     'id="zoomIn"' in html and 'id="zoomReset"' in html,
        "proof_summary":     'id="proof"' in html,
        "style_block":       "<style>" in html,
        "script_module":     '<script type="module">' in html,
        "steps_9":           html.count('class="step"') >= 9,
    }

    failed = [k for k, v in checks.items() if not v]

    slot_report = {}
    for name in SECTION_ORDER:
        filled = f"e2_filled_{name}"
        exists = (BASE / filled).exists()
        slot_report[name] = "filled" if exists else "template_only"

    output = {
        "stage": "E4",
        "status": "fail" if failed else "pass",
        "file_written": str(out_path),
        "file_size": len(html),
        "dom_checks": checks,
        "dom_failures": failed,
        "slot_fill_report": slot_report,
        "errors": [f"missing DOM element: {f}" for f in failed],
    }

    out_meta = BASE / "e4-output.json"
    out_meta.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"E4: {'PASS' if not failed else 'FAIL'} — {len(html)} chars, {len(html.splitlines())} lines")
    if failed:
        for f in failed:
            print(f"  FAIL: {f} missing")
        sys.exit(1)
    for k, v in checks.items():
        print(f"  {k}: {'✓' if v else '✗'}")
    print(f"E4 written to {out_path}")

if __name__ == "__main__":
    main()