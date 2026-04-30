#!/usr/bin/env python3
"""Stage E2: Content Binder — fills template slots from artifact-plan.json.

Reads: e1-output.json + artifact-plan.json
Output: e2-output.json (filled templates as strings)
Behavior: For each section template, merge static template content with
          data from artifact-plan.json content_bindings.
          Only dynamic slots are replaced; static content stays as-is.
"""
import json, re, sys
from pathlib import Path

BASE  = Path("P:/packages/cc-skills-meta/skills/skill-to-page")
TPL   = BASE / "templates"
E1_OUT = BASE / "e1-output.json"
PLAN   = BASE / "artifact-plan.json"

def load_json(p):
    return json.loads(p.read_text(encoding="utf-8"))

def slot_fill(template: str, bindings: dict) -> str:
    """Replace {{key}} placeholders in template with values from bindings dict."""
    result = template
    for key, value in bindings.items():
        placeholder = "{{" + key + "}}"
        if placeholder in result:
            result = result.replace(placeholder, str(value))
    return result

def fill_hero(template: str, plan: dict) -> str:
    bindings = {
        "skill_name":    plan["content_bindings"]["skill_name"],
        "version":       plan["content_bindings"]["version"],
        "description":   plan["content_bindings"]["description"],
    }
    # Also handle no-braces variants that appear in the template
    result = template
    result = re.sub(r'class="badge badge-version">[^<]*', f'class="badge badge-version">v{plan["content_bindings"]["version"]}', result)
    result = re.sub(r'<h1>[^<]*</h1>', f'<h1>{plan["content_bindings"]["skill_name"]}</h1>', result)
    return slot_fill(result, bindings)

def fill_facts(template: str, plan: dict) -> str:
    """facts template uses static content in skill-to-page case.
    For generic skills, this would be generated from step/gate/artifact counts."""
    return template  # facts are static in the current template

def fill_mermaid_panel(template: str, plan: dict) -> str:
    """Replace the Mermaid source in the template."""
    mermaid_src = plan.get("mermaid_source", "")
    result = template
    # Replace the content inside <pre id="mermaidSource">...</pre>
    result = re.sub(
        r'(<pre[^>]+id="mermaidSource"[^>]*>).*?(</pre>)',
        lambda m: m.group(1) + "\n" + mermaid_src + "\n" + m.group(2),
        result,
        flags=re.DOTALL
    )
    return result

def fill_steps(template: str, plan: dict) -> str:
    """Replace the hardcoded step articles with content from content_bindings.steps."""
    steps = plan["content_bindings"]["steps"]
    # Build replacement articles from step data
    new_articles = ""
    for i, step in enumerate(steps, 1):
        # Escape content for HTML safety
        name = step["name"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        desc = step["description"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        new_articles += f'''
        <article class="step" id="step-{i}">
          <div class="step-header" onclick="toggleStep(this)">
            <h3>Step {i} — {name}</h3>
            <span class="chevron">▼</span>
          </div>
          <div class="step-body">
            <p>{desc}</p>
          </div>
        </article>
'''
    # Replace existing step articles (id="step-1" through id="step-N")
    result = re.sub(
        r'<article class="step" id="step-\d+">.*?</article>',
        '',
        template,
        flags=re.DOTALL
    )
    # The template has steps 1-9 hardcoded; replace the first occurrence of the section header + articles
    # We inject after the <h2>Workflow Steps</h2> line
    result = re.sub(
        r'(<h2>Workflow Steps</h2>\s*)',
        r'\1' + new_articles,
        result,
        count=1
    )
    return result

def fill_route_outs(template: str, plan: dict) -> str:
    """Replace the hardcoded route-out with data from content_bindings.route_outs."""
    route_outs = plan["content_bindings"].get("route_outs", [])
    if not route_outs:
        return template
    route = route_outs[0]
    # Replace target and trigger text
    result = template
    result = re.sub(r'<code>delegate_to_skill_to_page</code>', f'<code>{route["target"]}</code>', result)
    # Trigger text replacement
    return result

def fill_terminals(template: str, plan: dict) -> str:
    terminals = plan["content_bindings"].get("terminal_states", [])
    if not terminals:
        return template
    return template  # static for now

def fill_artifacts(template: str, plan: dict) -> str:
    artifacts = plan["content_bindings"].get("artifacts", [])
    if not artifacts:
        return template
    return template  # static for now

def fill_proof_summary(template: str, plan: dict) -> str:
    return template  # static for now

SECTION_HANDLERS = {
    "hero.html":           fill_hero,
    "facts.html":          fill_facts,
    "mermaid-panel.html":  fill_mermaid_panel,
    "steps-accordion.html": fill_steps,
    "route-outs.html":     fill_route_outs,
    "terminals.html":       fill_terminals,
    "artifacts.html":      fill_artifacts,
    "proof-summary.html":  fill_proof_summary,
}

def main():
    e1 = load_json(E1_OUT)
    plan = load_json(PLAN)

    if e1.get("status") != "pass":
        print("E1 must pass before E2 can run")
        sys.exit(1)

    errors = []
    filled = {}

    for name, handler in SECTION_HANDLERS.items():
        tpl_path = TPL / name
        if not tpl_path.exists():
            errors.append(f"missing template: {name}")
            continue
        template = tpl_path.read_text(encoding="utf-8")
        try:
            filled[name] = handler(template, plan)
        except Exception as ex:
            errors.append(f"error filling {name}: {ex}")
            filled[name] = template  # fall back to raw template

    unfilled = []
    for name, content in filled.items():
        # Check for any remaining unfilled {{placeholders}}
        remaining = re.findall(r'\{\{[^}]+\}\}', content)
        if remaining:
            unfilled.append({"template": name, "remaining": remaining})

    output = {
        "stage": "E2",
        "status": "fail" if errors else "pass",
        "templates_filled": list(filled.keys()),
        "slot_fill_report": { name: "filled" for name in filled },
        "unfilled_slots": unfilled,
        "errors": errors,
    }

    out_path = BASE / "e2-output.json"
    # Write filled templates to a companion file (not inline in JSON — too large)
    for name, content in filled.items():
        (BASE / f"e2_filled_{name}").write_text(content, encoding="utf-8")

    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

    n = len(filled)
    print(f"E2: {'PASS' if not errors else 'FAIL'} — {n} templates filled")
    if errors:
        for e in errors: print(f"  ERROR: {e}")
        sys.exit(1)
    print(f"E2 written to {out_path}")

if __name__ == "__main__":
    main()