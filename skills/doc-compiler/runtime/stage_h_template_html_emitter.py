#!/usr/bin/env python3
"""Stage H: Template HTML Emitter for doc-compiler.

Reads artifact-plan.json (Stage G) and templates/.
Emits index.html by filling templates with content bindings.
Also emits assembled CSS and JS blocks as artifact files.
"""
import json, re, sys
from pathlib import Path

BASE = Path("P:/packages/cc-skills-meta/skills/doc-compiler")
TPL  = BASE / "templates"
PLAN = BASE / "artifact-plan.json"
OUT_HTML = BASE / "index.html"
OUT_CSS  = BASE / "assembled.css"
OUT_JS   = BASE / "assembled.js"


def load_json(p: Path) -> dict:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def read_template(name: str) -> str:
    path = TPL / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def fill(template: str, bindings: dict) -> str:
    """Fill {{placeholders}} in template with bindings dict values."""
    result = template
    for key, value in bindings.items():
        placeholder = "{{" + key + "}}"
        if isinstance(value, list):
            # Lists are handled per-section, just stringify for now
            result = result.replace(placeholder, str(value))
        elif isinstance(value, dict):
            result = result.replace(placeholder, json.dumps(value))
        else:
            result = result.replace(placeholder, str(value))
    return result


def fill_steps_section(steps: list) -> str:
    """Fill the steps accordion section with step data."""
    template = read_template("steps-accordion.html")
    if not template:
        return "<!-- steps section unavailable -->"

    steps_html = ""
    for i, step in enumerate(steps, 1):
        step_id = step.get("id", f"step-{i}")
        name = step.get("name", f"Step {i}")
        description = step.get("description", "")
        display_name = step.get("display_name", name)

        step_block = f"""
        <article class="step" id="{step_id}">
          <button class="step-header" onclick="toggleStep('{step_id}')" aria-expanded="false">
            <span class="step-index">{i}.</span>
            <span class="step-name">{display_name}</span>
            <span class="step-chevron">▾</span>
          </button>
          <div class="step-body" id="{step_id}-body">
            <p class="step-description">{description}</p>
          </div>
        </article>"""
        steps_html += step_block

    return template.replace("{{steps_content}}", steps_html)


def fill_route_outs_section(route_outs: list) -> str:
    """Fill the route-outs section."""
    template = read_template("route-outs.html")
    if not route_outs:
        return ""

    items_html = ""
    for r in route_outs:
        target = r.get("target", r.get("trigger", ""))
        trigger = r.get("trigger", "")
        desc = r.get("description", "")
        items_html += f"""
        <li class="route-out-item">
          <code class="route-target">{target}</code>
          <span class="route-trigger">{trigger}</span>
          <span class="route-desc">{desc}</span>
        </li>"""

    return template.replace("{{route_outs_content}}", items_html)


def fill_terminals_section(terminals: list) -> str:
    """Fill the terminal states section."""
    template = read_template("terminals.html")
    if not terminals:
        return ""

    items_html = ""
    for t in terminals:
        name = t.get("name", "")
        desc = t.get("description", "")
        items_html += f"""
        <li class="terminal-item">
          <span class="terminal-name">{name}</span>
          <span class="terminal-desc">{desc}</span>
        </li>"""

    return template.replace("{{terminals_content}}", items_html)


def fill_artifacts_section(artifacts: list) -> str:
    """Fill the artifacts section."""
    template = read_template("artifacts.html")
    if not artifacts:
        return ""

    cards_html = ""
    for a in artifacts:
        name = a.get("name", "")
        path_val = a.get("path", "")
        desc = a.get("description", "")
        cards_html += f"""
        <div class="artifact-card">
          <span class="artifact-name">{name}</span>
          <code class="artifact-path">{path_val}</code>
          <span class="artifact-desc">{desc}</span>
        </div>"""

    return template.replace("{{artifacts_content}}", cards_html)


def fill_diagram_panel(diagrams_json_path: str) -> str:
    """Fill the Mermaid diagram panel with diagram data."""
    template = read_template("mermaid-panel.html")

    # Read diagrams.json to get the .mmd content
    diagrams_path = BASE / "diagrams.json"
    diagrams_data = load_json(diagrams_path)
    diagrams = diagrams_data.get("diagrams", [])

    # Build diagram tabs HTML
    tabs_html = ""
    panels_html = ""

    for i, diag in enumerate(diagrams):
        diagram_id = diag.get("diagram_id", f"diagram-{i}")
        diagram_type = diag.get("diagram_type", "")
        caption = diag.get("caption", "")
        mmd_content = diag.get("mmd_content", "")
        palette_hint = diag.get("palette_hint", "tailwind-modern")

        active = "active" if i == 0 else ""
        tabs_html += f"""
        <button class="diagram-tab {active}" data-diagram="{diagram_id}" onclick="switchDiagram('{diagram_id}')">
            {diagram_type}
        </button>"""

        panels_html += f"""
        <div class="diagram-panel" id="panel-{diagram_id}" style="display:{('block' if i == 0 else 'none')}">
            <pre id="mermaidSource" class="mermaid-source">{mmd_content}</pre>
            <div class="diagram-viewport" id="diagramViewport">
                <div class="diagram-stage" id="diagramStage"></div>
            </div>
            <div class="diagram-caption">{caption}</div>
        </div>"""

    # Build palette selector
    palettes_html = ""
    for palette in ["tailwind-modern", "github-dark", "nord", "one-dark-pro", "dracula", "material-ocean"]:
        palettes_html += f'<option value="{palette}">{palette}</option>'

    result = template
    result = result.replace("{{diagram_tabs}}", tabs_html)
    result = result.replace("{{diagram_panels}}", panels_html)
    result = result.replace("{{palette_options}}", palettes_html)
    result = result.replace("{{diagram_count}}", str(len(diagrams)))

    return result


def fill_proof_section() -> str:
    """Fill the proof summary section."""
    template = read_template("proof-summary.html")
    # Proof section is filled at runtime from proof-metadata.json
    return template.replace("{{proof_content}}", "Documentation proof metadata loaded from proof-metadata.json")


def assemble_css() -> str:
    """Assemble all CSS into one block."""
    css_parts = []

    for fname in ["shared-css.css", "section-css.css", "toc-css.css", "diagram-css.css"]:
        content = read_template(fname)
        if content:
            css_parts.append(content)

    return "\n".join(css_parts)


def assemble_js() -> str:
    """Assemble all JS into one block."""
    js_parts = []

    for fname in ["shared-scripts.js", "diagram-scripts.js"]:
        content = read_template(fname)
        if content:
            js_parts.append(content)

    return "\n".join(js_parts)


def main() -> None:
    if not PLAN.exists():
        print(f"ERROR: {PLAN} not found. Run Stage G first.", file=sys.stderr)
        sys.exit(1)

    plan = load_json(PLAN)
    bindings = plan.get("content_bindings", {})

    # Load base shell
    base_shell = read_template("base-shell.html")
    if not base_shell:
        print("ERROR: templates/base-shell.html not found", file=sys.stderr)
        sys.exit(1)

    # Fill base shell placeholders
    html = base_shell
    html = html.replace("{{skill_name}}", bindings.get("name", "Documentation"))
    html = html.replace("{{version}}", bindings.get("version", "0.0.0"))

    # Build page content
    main_content = ""

    # Hero section
    hero_tpl = read_template("hero.html")
    hero = fill(hero_tpl, {
        "skill_name": bindings.get("name", ""),
        "version": bindings.get("version", "0.0.0"),
        "description": bindings.get("description", ""),
        "enforcement": bindings.get("enforcement", "strict"),
        "status": bindings.get("status", "active"),
    })
    main_content += hero + "\n"

    # Facts section
    facts_tpl = read_template("facts.html")
    triggers = bindings.get("triggers", [])
    if triggers:
        triggers_html = ", ".join(f"<code>{t}</code>" for t in triggers)
        facts = fill(facts_tpl, {"triggers_html": triggers_html})
        main_content += facts + "\n"

    # Search UI
    main_content += read_template("search-ui.html") + "\n"

    # Diagram panel
    main_content += fill_diagram_panel("diagrams.json") + "\n"

    # Steps accordion
    steps = bindings.get("steps", [])
    if steps:
        main_content += fill_steps_section(steps) + "\n"

    # Route outs
    route_outs = bindings.get("route_outs", [])
    if route_outs:
        main_content += fill_route_outs_section(route_outs) + "\n"

    # Terminals
    terminals = bindings.get("terminal_states", [])
    if terminals:
        main_content += fill_terminals_section(terminals) + "\n"

    # Artifacts
    artifacts = bindings.get("artifacts", [])
    if artifacts:
        main_content += fill_artifacts_section(artifacts) + "\n"

    # Proof section
    main_content += fill_proof_section() + "\n"

    # Inject main content into shell
    # Find where <div class="main-content"> goes and insert content
    html = html.replace("{{main_content}}", main_content)

    # CSS block
    css = assemble_css()
    html = html.replace("{{css_block}}", css)

    # JS block
    js = assemble_js()
    html = html.replace("{{js_block}}", js)

    # Write index.html
    OUT_HTML.write_text(html, encoding="utf-8")

    # Also write assembled CSS/JS as separate artifacts
    OUT_CSS.write_text(css, encoding="utf-8")
    OUT_JS.write_text(js, encoding="utf-8")

    # Validate DOM elements
    checks = {
        "doctype":          html.startswith("<!DOCTYPE html>"),
        "toc_toggle":       'id="tocToggle"' in html,
        "toc_element":      'id="toc"' in html and 'class="toc"' in html,
        "mermaid_source":   'id="mermaidSource"' in html,
        "resize_handle":    'id="diagramResizeHandle"' in html,
        "theme_toggle":     'id="themeToggle"' in html,
        "search_input":     'id="searchInput"' in html,
        "diagram_viewport":  'id="diagramViewport"' in html,
        "diagram_stage":     'id="diagramStage"' in html,
        "zoom_controls":     'id="zoomIn"' in html and 'id="zoomReset"' in html,
        "proof_summary":    'id="proof"' in html,
        "style_block":      "<style>" in html,
        "script_module":    '<script type="module">' in html,
        "steps_present":    html.count('class="step"') >= 1,
    }

    failed = [k for k, v in checks.items() if not v]

    output = {
        "stage": "H",
        "status": "pass" if not failed else "fail",
        "file_written": str(OUT_HTML),
        "file_size": len(html),
        "dom_checks": checks,
        "dom_failures": failed,
        "errors": [f"missing DOM element: {f}" for f in failed]
    }

    print(f"Stage H: {'PASS' if not failed else 'FAIL'} — {len(html)} chars, {len(html.splitlines())} lines")
    if failed:
        for f in failed:
            print(f"  MISSING: {f}")
    for k, v in checks.items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")
    print(f"Written: {OUT_HTML}")
    print(f"Written: {OUT_CSS}")
    print(f"Written: {OUT_JS}")
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()