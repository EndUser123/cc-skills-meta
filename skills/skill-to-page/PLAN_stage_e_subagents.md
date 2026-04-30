# Plan: Refactor skill-to-page Stage E into sub-agent pipeline

## Problem

Stage E (HTML Emitter) is a "big bang" LLM call that generates the entire HTML file in one pass. Bugs (wrong selectors, missing IDs, broken CSS) only surface in Stage F/G/H — 3 stages later. Each fix requires re-running the full pipeline.

## Solution: Split Stage E into 4 focused sub-agents

### Architecture

```
artifact-plan.json  →  E1 (Template Loader)  →  E1-output.json
                                                    ↓
                                              E2 (Content Binder)  →  E2-output.json
                                                                    ↓
                                                              E3 (CSS/JS Assembler)  →  E3-output.json
                                                                                    ↓
                                                                              E4 (HTML Writer)  →  index.html
                                                                                                  ↓
                                                                                              F/G/H validators
```

Each sub-agent is small, focused, and produces JSON for the next stage.

---

## E1: Template Loader

**Role:** Verify all template files exist and report their structure.

**Input:** `artifact-plan.json` (reads `template_version`)

**Output:** `e1-output.json`
```json
{
  "stage": "E1",
  "template_version": "v1",
  "templates_loaded": {
    "base-shell": "templates/base-shell.html",
    "toc": "templates/toc.html",
    ...
  },
  "structure_elements": {
    "toc_toggle": "<button id=\"tocToggle\"",
    "toc_element": "<nav id=\"toc\" class=\"toc\"",
    "mermaid_source": "<pre id=\"mermaidSource\"",
    "resize_handle": "<div id=\"diagramResizeHandle\""
  },
  "errors": []
}
```

**Behavior:** Reads all 18 template files, verifies required DOM elements are present, reports missing templates or broken structure. If errors, writes them to `e1-output.json.errors` and exits 1. If clean, passes to E2.

**Verification gate:** E1 fails if any required template is missing OR any required DOM element (tocToggle, nav#toc, mermaidSource, resizeHandle) is absent from templates.

---

## E2: Content Binder

**Role:** Fill content slots in section templates using `artifact-plan.json` data.

**Input:** `e1-output.json` + `artifact-plan.json`

**Output:** `e2-output.json`
```json
{
  "stage": "E2",
  "slots_filled": {
    "hero_name": "skill-to-page",
    "hero_version": "2.0.0",
    "hero_description": "...",
    "steps": [ ...9 step objects... ],
    "route_outs": [ ... ],
    "terminals": [ ... ],
    "artifacts": [ ... ],
    "mermaid_source": "flowchart TD\n  ..."
  },
  "unfilled_slots": [],
  "errors": []
}
```

**Behavior:** Reads section templates (hero.html, steps-accordion.html, etc.), binds content from `artifact-plan.json.content_bindings`. Every slot must be filled or reported. Produces a "filled templates" dict where each key is a template name and value is the HTML with slots resolved.

**Verification gate:** E2 fails if any required slot (step name, step description, mermaid_source, artifact path) is empty or missing from artifact-plan.json.

---

## E3: CSS/JS Assembler

**Role:** Concatenate all CSS and JS files in correct order.

**Input:** `e2-output.json` + all template CSS/JS files

**Output:** `e3-output.json`
```json
{
  "stage": "E3",
  "css_concatenated": true,
  "css_parts": ["shared-css.css", "toc-css.css", "section-css.css", "diagram-css.css"],
  "js_concatenated": true,
  "js_parts": ["shared-scripts.js", "diagram-scripts.js"],
  "palettes_inlined": "tailwind-modern",
  "mermaid_init_config": { "startOnLoad": false, "securityLevel": "loose" },
  "errors": []
}
```

**Behavior:** Concatenates CSS files in order, concatenates JS files in order, inlines the selected `mermaid-palettes.json` palette into the JS. Writes assembled CSS and JS as strings in `e3-output.json`.

**Verification gate:** E3 fails if any CSS/JS file is missing or if palette key doesn't exist in mermaid-palettes.json.

---

## E4: HTML Writer

**Role:** Assemble all parts into final index.html.

**Input:** `e3-output.json` + `e2-output.json` + `e1-output.json`

**Output:** `index.html` + `e4-output.json`
```json
{
  "stage": "E4",
  "file_written": "index.html",
  "file_size": 69558,
  "html_structure": {
    "doctype": true,
    "head": true,
    "toc_toggle": true,
    "toc_sidebar": true,
    "main_content": true,
    "style_block": true,
    "script_modules": 2
  },
  "slot_fill_report": {
    "hero": "filled",
    "facts": "filled",
    "steps": "filled (9 steps)",
    "route_outs": "filled (1 route-out)",
    "terminals": "filled (1 terminal)",
    "artifacts": "filled (4 artifacts)",
    "proof_summary": "filled"
  }
}
```

**Behavior:** Takes assembled CSS + JS + filled templates, assembles into a valid HTML file, writes to `index.html`.

**Verification gate:** E4 fails if file size is 0 or if required DOM elements are missing from output.

---

## Changes to skill-to-page pipeline

### SKILL.md updates

1. **Stage E description** changes from "LLM assembles HTML from prose rules" to "Python assembler + 4 sub-agents"
2. **Add `template_version: "v1"` field** to artifact-plan.json schema
3. **Add E1-E4 contract** to SKILL.md: each sub-agent's input, output, and verification gate
4. **Remove** the long prose HTML/CSS/JS specifications from Stage E description (they live in template files now)

### New files

| File | Purpose |
|------|---------|
| `stage_e1_loader.py` | E1: verify templates exist and report structure |
| `stage_e2_binder.py` | E2: fill content slots from artifact-plan.json |
| `stage_e3_assembler.py` | E3: concatenate CSS/JS, inline palettes |
| `stage_e4_writer.py` | E4: assemble and write final HTML |
| `stage_e_runner.py` | Orchestrates E1→E2→E3→E4, handles errors |

### Template files (already exist, no changes needed)

All 18 template files in `templates/` are the source of truth for HTML structure. E1 only reads them — never modifies them.

---

## Why this is more robust

1. **Each stage is independently testable** — E1 can be run standalone to verify templates, E2 to verify bindings, etc.
2. **Failure is localized** — if E3 has a CSS concatenation bug, you fix E3 directly, not re-run the whole pipeline
3. **No LLM needed for infrastructure** — assembly (file reading, concatenation, string substitution) is deterministic Python; LLM only needed for E2 content binding
4. **Fast iteration** — `rebuild_index.py` already proves the template assembly works; E2 is the only part that needs LLM judgment
5. **Progressive validation** — each stage has a gate; problems are caught at the source, not 3 stages downstream

## Falsification condition

This would be wrong if: the template files diverge from what the SKILL.md prose describes, causing the assembled HTML to have wrong structure that E1-E4 can't detect. Mitigation: E1 has a `structure_elements` check that verifies required DOM elements are present.