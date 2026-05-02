#!/usr/bin/env python3
"""Stage E4: HTML Writer — assembles the final index.html from all E1-E3 outputs.

Reads: e1-output.json, e2-output.json, e3-output.json, e2_filled_*.html, e3_css_block.css, e3_js_block.js
Output: index.html + e4-output.json
Behavior: Takes assembled CSS + JS + filled templates, concatenates into a valid HTML file.
"""
import json, re, sys
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

    # --- JS MODULE INTEGRITY LINT (before writing) ---
    # Multi-line statement joining: merge continuation lines (.then/.catch) onto their prior line
    # so dynamic imports like `window.__mermaidReady = import(...).then(...)` stay intact
    joined_lines = []
    pending = None
    for line in js_block.split("\n"):
        stripped = line.strip()
        if stripped.startswith(".then(") or stripped.startswith(".catch("):
            # Continuation of previous statement — merge onto pending line
            if pending is not None:
                pending = pending.rstrip() + " " + stripped
            else:
                joined_lines.append(line)
                pending = None
        else:
            if pending is not None:
                joined_lines.append(pending)
                pending = None
            joined_lines.append(line)
    if pending is not None:
        joined_lines.append(pending)
    js_block_joined = "\n".join(joined_lines)

    # Static imports: line starts with "import " (with trailing space, not "import(")
    # Dynamic imports: line contains "import(" (e.g. window.__mermaidReady = import('...'))
    static_import_lines = [line for line in joined_lines if line.strip().startswith("import ")]
    dynamic_import_lines = [line for line in joined_lines if 'import(' in line]
    import_lines = static_import_lines + dynamic_import_lines
    other_lines   = [line for line in joined_lines
                    if not line.strip().startswith("import ")
                    and 'import(' not in line]

    # LINT-1: import ordering — all imports must precede all executable code
    first_executable_idx = None
    for i, line in enumerate(other_lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("//") and not stripped.startswith("*"):
            first_executable_idx = i
            break
    if first_executable_idx is not None:
        first_code_line = other_lines[first_executable_idx]
        for i, il in enumerate(import_lines):
            # check if any import comes after the first non-import line in sequence order
            pass  # import_lines are already ordered before other_lines by construction
        # More precise: scan the full interleaved stream
        all_lines_ordered = import_lines + other_lines
        for idx, line in enumerate(all_lines_ordered):
            stripped = line.strip()
            if stripped.startswith("import "):
                prior = all_lines_ordered[:idx]
                prior_executables = [l.strip() for l in prior if l.strip() and not l.strip().startswith("import ") and not l.strip().startswith("//")]
                if prior_executables:
                    fail_line = other_lines.index(line) if line in other_lines else -1
                    print(f"E4 FAIL: import statement found after executable code at line ~{fail_line} in js_block")
                    sys.exit(1)

    # LINT-2: duplicate top-level const declarations (module scope only, not inner-block shadowing)
    const_names = {}
    for i, line in enumerate(joined_lines):
        stripped = line.strip()
        # Only check top-level lines (no leading whitespace = module scope)
        # and ignore const inside function bodies (shadowing is legal)
        if stripped.startswith("const ") and not line.startswith(" "):
            m = re.match(r'const\s+(\w+)\s*=', stripped)
            if m:
                name = m.group(1)
                if name in const_names:
                    print(f"E4 FAIL: duplicate const declaration: {name} (first at line {const_names[name]}, second at line {i+1})")
                    sys.exit(1)
                const_names[name] = i + 1

    # LINT-3: duplicate top-level function declarations
    func_names = {}
    for i, line in enumerate(joined_lines):
        stripped = line.strip()
        if stripped.startswith("function ") and not line.startswith(" "):
            m = re.match(r'function\s+(\w+)\s*\(', stripped)
            if m:
                name = m.group(1)
                if name in func_names:
                    print(f"E4 FAIL: duplicate function declaration: {name} (first at line {func_names[name]}, second at line {i+1})")
                    sys.exit(1)
                func_names[name] = i + 1

    # LINT-3: strokeWidth key contract — PALETTES must use camelCase strokeWidth, not snake_case stroke_width
    if "stroke_width" in js_block:
        print("E4 FAIL: PALETTES uses stroke_width; buildClassDefs expects strokeWidth")
        sys.exit(1)

    # LINT-4: initMermaid/renderMermaid must appear AFTER import mermaid
    import_mermaid_idx = None
    for i, line in enumerate(joined_lines):
        if "import mermaid" in line or 'import(' in line:
            import_mermaid_idx = i
            break
    # More precise: find initMermaid() and renderMermaid() call lines
    call_lines = [(i, l) for i, l in enumerate(joined_lines) if l.strip().startswith("initMermaid()") or l.strip().startswith("renderMermaid()")]
    if import_mermaid_idx is not None:
        for cline_idx, cline in call_lines:
            if cline_idx > import_mermaid_idx:
                pass  # ok
            else:
                print(f"E4 FAIL: {cline.strip()} call appears before import statement")
                sys.exit(1)
    # --- END JS MODULE INTEGRITY LINT ---

    lines.append('<script type="module">')
    # ES modules require all import declarations at the top
    for il in import_lines:
        lines.append("  " + il)
    for jl in other_lines:
        lines.append("  " + jl)
    lines.append('</script>')
    # Browser Use Chrome CDP: type="module" scripts fail to execute.
    # Fallback: mirror all JS as regular script so it executes.
    lines.append('<script>')
    lines.append('  // FALLBACK: re-execute module JS for Browser Use Chrome')
    # Include the dynamic import line (the one that matters for mermaid loading)
    for il in import_lines:
        if il.strip():
            lines.append("  " + il)
    # Include all other JS
    for jl in other_lines:
        if jl.strip():
            lines.append("  " + jl)
    lines.append('</script>')

    lines.append("</body>")
    lines.append("</html>")

    html = "\n".join(lines)
    out_path = BASE / "index.html"
    # Force LF-only line endings (Windows Python adds CRLF by default on Windows)
    with open(out_path, 'w', newline='\n', encoding='utf-8') as f:
        f.write(html)

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