---
name: skill-to-page
version: 2.0.0
description: Transform a skill's SKILL.md into a navigable, verified index.html with Mermaid diagrams, TOC, search, viewport controls, provenance, and proof-oriented verification.
category: documentation
enforcement: strict
workflow_steps:
  - read_skill_source
  - extract_workflow_model
  - detect_source_gaps
  - design_mermaid_diagram
  - mermaid_critic_review
  - generate_html
  - browser_verify_artifact
  - artifact_critic_review
  - emit_proof_metadata
triggers:
  - '/skill-to-page'
  - 'create index.html for'
  - 'skill to page'
  - 'document this skill'
argument-hint: <target-skill-name>
context: main
user-invocable: true
depends_on_skills: []
requires_tools:
  - browser-harness  # CDP-based browser verification in Step 7
aliases: []
status: active
---

# /skill-to-page — Skill to HTML Artifact

Transforms a skill's `SKILL.md` into a self-contained, navigable, browser-verified `index.html` page and associated proof metadata.

## When to Use

- skill-craft routes here during EXECUTING when HTML output is needed
- Any skill needs a browsable documentation page
- Converting skill documentation to shareable/viewable format
- Producing a verified artifact that faithfully represents skill workflow, routing, and outputs

## Input Contract

```bash
/skill-to-page <target-skill-name>
# Example: /skill-to-page go
```

**Reads:** `P:/.claude/skills/{target}/SKILL.md`
**Outputs:**
- `P:/.claude/skills/{target}/index.html` — written alongside target skill source (documentation artifact, not runtime state)
- `P:/.claude/.artifacts/{terminal_id}/skill-to-page/{target}/artifact-proof.json` (recommended)
- `P:/.claude/.artifacts/{terminal_id}/skill-to-page/{target}/workflow-model.json` (recommended)
- `P:/.claude/.artifacts/{terminal_id}/skill-to-page/{target}/diagram.mmd` (recommended)

---

## Workflow

### Step 1: Read Skill Source

Read the target skill's `SKILL.md` completely.

Extract at minimum:

- frontmatter
- `workflow_steps`
- description
- triggers
- key sections
- prose-described routing
- checklists / gating questions
- terminal states
- artifacts emitted
- referenced sub-skills
- verification expectations

Do not begin diagram generation yet.

### Step 2: Extract Workflow Model

Build a normalized internal workflow model from the source before generating either Mermaid or HTML.

Minimum model shape:

```json
{
  "skill_name": "string",
  "version": "string",
  "steps": [
    {
      "id": "stable-step-id",
      "index": 1,
      "name": "read_skill_source",
      "display_name": "Read Skill Source",
      "description": "string",
      "kind": "step|decision|route|terminal|artifact",
      "conditions": [],
      "inputs": [],
      "outputs": [],
      "routes_to": [],
      "artifacts_emitted": []
    }
  ],
  "decision_points": [],
  "route_outs": [],
  "terminal_states": [],
  "artifacts": [],
  "gaps": [],
  "ambiguities": []
}
```

This workflow model is the source of truth for:
- Mermaid diagram generation
- accordion section generation
- TOC generation
- verification coverage checks
- proof metadata

Never generate Mermaid and HTML independently from unstructured prose if a workflow model has not first been built.

### Step 3: Detect Source Gaps

Cross-check the source for mismatches before rendering.

Mandatory checks:

1. **Prose-only routing**
   - If prose says "route to /planning", "delegate to /code", or similar, but this is not reflected in `workflow_steps`, add it to the workflow model as a route or decision.

2. **Checklist-implied branching**
   - If a checklist question implies a Yes/No path (e.g. "Do I need explore first?"), model it as a decision gate.

3. **Conditional steps shown as unconditional**
   - If a step only runs under conditions, mark it conditional in the workflow model and diagram.

4. **Missing step descriptions**
   - If a `workflow_steps` entry has no prose description, generate a brief, faithful description before HTML generation.

5. **Terminal states not represented**
   - If the skill emits end states, promises, or blocking outcomes, ensure they appear in the workflow model.

6. **Artifact outputs not represented**
   - If the skill writes files, reports, JSON, or tokens, ensure those outputs are represented in the model.

7. **Naming mismatches**
   - If a prose label differs from the actual `workflow_steps` entry, preserve the source-of-truth step name and optionally use prose wording as display text.

If gaps remain unresolved, record them under `ambiguities` in the workflow model and surface them in proof metadata.

**Gate:** `ambiguities.length === 0 OR ambiguities_recorded === true` — unresolved gaps must be explicitly recorded, not silently ignored.

### Step 4: Design Mermaid Diagram

Generate Mermaid from the normalized workflow model, not directly from raw prose.

**Layout rules:**

| Rule | Why | Enforce with |
|------|-----|--------------|
| Direction matters | TD for vertical workflows, LR for state-machine-like flows | `flowchart TD` or `flowchart LR` |
| Group by phase | Related concepts should share rank or proximity | Node order / rank alignment |
| Avoid crossings | Crossings reduce readability | Reorder nodes or insert invisible guides |
| Color-code intent | Forward vs route-out vs terminal is easier to scan | Distinct classDefs |
| Smooth curves | Improves readability in dense graphs | `curve: 'basis'` (mandatory, not optional) |
| Spacing matters | Avoid visual fusion and excessive gaps | `nodeSpacing: 40`, `rankSpacing: 50`, `padding: 16` |
| Width control | Prevent jagged wrapping | responsive container + `useMaxWidth: true` |
| Label length | Long labels create Jagged edges and break zoom readability | Max 40 chars per node; use `wrap()` for longer labels; never exceed 2 visual lines |

**Label length enforcement:**

- Target: ≤ 40 characters per node label
- If label exceeds 40 chars: truncate to 40 and append `wrap()`
- If wrapped label exceeds 2 visual lines: split into two nodes or use a shorter phrase
- `curve: 'basis'` is mandatory on every diagram — omit it only if the graph has ≤ 5 nodes

**Node shape choices:**
- Start/End: rounded pill
- Step: rectangle
- Decision: diamond
- Route-out: distinct class
- Terminal state: pill or emphasized terminal node
- Artifact/data: boxed state node

The diagram must reflect actual decision structure, route-outs, and terminal states.

### Step 5: Mermaid Critic Review (MANDATORY GATE)

```
agent: general-purpose
purpose: Validate Mermaid diagram for skill-to-page workflow artifact
inputs:
  - diagram.mmd           # Raw Mermaid source
  - workflow-model.json   # Source of truth for what diagram must represent
checks:
  1. Start-to-end traceability — trace from Start to every terminal without lifting your pen
  2. Edge crossings — count crossing pairs; flag if > 0
  3. Label clarity — every node label is self-explanatory standing alone
  4. Non-forward edge labeling — every edge that is not a forward/pass has an explicit condition label
  5. Readability at 50% zoom — all text legible, no overlapping nodes
  6. Mermaid syntax validity — parse with no errors
  7. Coverage of all workflow model steps — every step in workflow-model.json appears as a node
  8. Coverage of all route-outs — every route_out in workflow model appears in diagram
  9. Coverage of all terminal states — every terminal state in workflow model appears
  10. Coverage of all decision points — every decision_point in workflow model is a diamond or branch
  11. Explicit color: in each classDef — every classDef has a color: attribute (not just fill:/stroke:)
  12. Theme-safe text colors:
      - Dark theme: text color must have ≥ 4.5:1 contrast ratio against node fill (light text on dark fill)
      - Light theme: text color must be dark enough to read on light fills (no #000 on white without contrast)
      - Verify both themes; reject any color: value that is purely #000 with no theme-specific override
gate: crossings == 0 AND syntax_errors == [] AND legibility_score >= 0.8 AND missing_steps == [] AND missing_route_outs == [] AND missing_terminal_states == [] AND dark_theme_contrast_ok == true AND light_theme_text_readable == true
```

**Note:** `agent: general-purpose` is the canonical subagent type for inline critic agents, consistent with skill-craft's own mermaid critic block. This string is an established convention, not an arbitrary value. The `subagent_type` field is intentionally omitted in favor of inline agent dispatch.

If the critic fails, fix the workflow model or Mermaid before proceeding.

**Error handling:** If the agent dispatch fails or returns an error, record the error in the proof metadata and fail the step with a descriptive message. Infrastructure failures (agent timeout, browser launch failure) are distinct from critic-gate failures — report the exact failure mode.

### Step 6: Generate HTML

Build `index.html` from the workflow model.

**Page structure (in order):**

1. **Hero card** — skill name, version badge, one-line description of what this skill does
2. **Quick Facts** — 5–7 bullets: core capabilities (gates, artifact types, browser verification count, etc.)
3. **Mermaid diagram section** (with zoom/pan controls)
4. **Workflow Steps** — accordion per step, outcome-focused title + description
5. **Route Outs** — distinct section with each route-out's target and trigger condition
6. **Terminal States** — distinct section with each terminal's description
7. **Artifacts** — card per artifact with path + copy-to-clipboard button
8. **Proof Summary** — scannable card: coverage metrics, browser verification results, gate pass/fail status

**Required elements:**

- page header with skill name/version badge
- generated TOC (collapsible sidebar)
- Mermaid diagram with zoom/pan/reset controls
- accordion per workflow step (open/close on click)
- routing/decision visibility
- terminal states section
- artifact outputs section with download/copy
- theme toggle (dark/light)
- search UI (filters step sections)
- proof/provenance metadata section (compact)
- responsive layout (mobile: hamburger TOC, single column)
- accessible navigation (ARIA labels, focus-visible)
- copy-to-clipboard for all file paths (button per path)

**Artifact cards:** Each artifact gets a card with:
- Artifact type and description
- File path in a `<code>` block
- "Copy path" button that writes path to clipboard
- Link to open/download where applicable

**Proof Summary card** (placed after the diagram, before step accordions):
Show as a compact grid: skill name, version, steps count, gate count, route-outs, terminal states, browser verification status (all 13 checks), coverage percentages.

**Style requirements:**

- **Fonts:** Inter (prose/body) + JetBrains Mono (code/paths/gates). Load via Google Fonts. This improves readability and gives the page a more intentional, premium feel.
- **4-level type system:** page title (h1), section title (h2), body, metadata — reduces visual noise.
- **Code/path blocks:** dark inset surface (`#0d1017` background), `1px solid` border, compact padding. Monospace throughout so mechanical parts stand out instantly.
- **Section cards:** subtle gradient background, `1px solid` border with slight transparency, `8-12px` radius, soft shadow. Not flat blocks.
- **Gate/terminal/route badges:** stronger contrast and bold weight — functional decision points should pop visually. Gate: warm amber tones. Route: purple. Terminal: green.
- **Artifact/output sections:** distinct "console card" treatment — darker inset surface, stronger border, tabular spacing.
- **Copy buttons:** on every `<pre>` block, every path `<code>` block, and every artifact path. Fade in on hover. Inline "Copied!" feedback.
- **`:target` highlighting:** when a section is linked via hash, flash a subtle box-shadow animation (`0 0 0 10px rgba(accent, 0)`) so direct links feel responsive.
- **Transitions:** subtle hover/focus transitions on buttons, TOC entries, accordion headers (`140ms ease`).
- **Output card treatment:** distinct surface for artifact cards and proof metadata — darker inset, accent-tinted border.

This structure gives readers immediate orientation (what this is, what it does, what it produces) before diving into the diagram and step details.

### Step 7: Browser Verify Artifact

**Not agent-portable** — this step requires visual judgment via screenshot and browser interaction. Do not dispatch to a subagent. The orchestrating LLM performs this step directly.

Before declaring success, verify the generated page behavior in-browser.

Mandatory checks:

1. File exists at target path
2. Mermaid renders successfully
3. Every TOC item points to an existing section
4. TOC toggle changes actual visible state — **verify initial state is aligned**: `body.classList.contains('toc-hidden')` must match `nav.classList.contains('collapsed')` at page load, before any click
5. Main content reflows correctly when TOC is hidden
6. Theme toggle rerenders Mermaid without losing viewport state
7. Zoom in/out/reset work
8. Drag-to-pan works when advanced viewport mode is enabled
9. Wheel zoom is cursor-centric and bound to `.mermaid-container`
10. Search finds expected sections
11. Accordion sections open/close correctly
12. No duplicate event listeners are bound
13. No console errors on load or core interactions

Visual verification is required for layout-affecting features.

**Timeout: 120000ms** for full verification suite. If any individual check exceeds 30s, fail the step with an actionable error rather than hanging. Common failure modes: browser launch failure (check CDP URL), Mermaid render stall (try `mermaid.run()` re-invoke), page load timeout (increase wait before checks). Report the exact CDP error or stall point in the failure message.

### Step 8: Artifact Critic Review

```
agent: general-purpose
purpose: Verify index.html fidelity to workflow model and browser behavior
inputs:
  - index.html            # The generated HTML artifact
  - workflow-model.json   # Source of truth for workflow structure
  - diagram.mmd           # Mermaid source (for cross-reference)
checks:
  fidelity:
    - HTML faithfully represents the workflow model
    - Every workflow step appears as a section (check: workflow_steps.length vs section#workflow-step-* count)
    - All decision branches are visible as distinct accordion sections
    - All route-outs appear as distinct sections
    - All terminal states are visible
    - No behavior or route is invented without source support (blocking defect)
    - TOC is complete and logically ordered
  usability:
    - Artifact is usable without reading the Mermaid diagram
    - Page is usable without JavaScript for core reading flow (where practical)
  toc_toggle (blocking — must both pass):
    - At page load, before any click: nav.classList.contains('collapsed') === body.classList.contains('toc-hidden')
      → If false: toggle will be inverted; this is a blocking defect
    - Each click handler toggles both nav.collapsed AND body.toc-hidden atomically — never one without the other
      → If one toggles without the other: non-atomic update; this is a blocking defect
gate: no_invented_routes == true AND toc_initial_state_synced == true AND toc_handler_atomic == true
```

If the artifact critic finds fidelity or usability issues, revise the artifact and rerun verification.

### Step 9: Emit Proof Metadata

Emit proof metadata alongside the artifact.

Recommended files:

#### `workflow-model.json`
Normalized extracted workflow model.

#### `artifact-proof.json`
Example shape:

```json
{
  "skill_name": "go",
  "skill_version": "2.0.0",
  "source_path": "P:/.claude/skills/go/SKILL.md",
  "artifact_path": "P:/.claude/skills/go/index.html",
  "generated_at": "ISO-8601",
  "generator_skill_version": "2.0.0",
  "mermaid_version": "11",
  "coverage": {
    "workflow_steps_declared": 0,
    "workflow_sections_rendered": 0,
    "decision_points_detected": 0,
    "decision_points_rendered": 0,
    "route_outs_detected": 0,
    "route_outs_rendered": 0,
    "terminal_states_detected": 0,
    "terminal_states_rendered": 0
  },
  "browser_verification": {
    "mermaid_rendered": true,
    "toc_toggle_ok": true,
    "toc_links_ok": true,
    "theme_toggle_ok": true,
    "zoom_controls_ok": true,
    "drag_pan_ok": true,
    "search_ok": true,
    "accordion_ok": true,
    "console_errors": []
  },
  "critic_results": {
    "mermaid_gate_passed": true,
    "artifact_gate_passed": true,
    "unresolved_ambiguities": []
  }
}
```

If any ambiguity remains, record it explicitly rather than silently guessing.

---

## HTML Authoring Rules

### CSS Rules

| Rule | Why |
|------|-----|
| No duplicate selectors | Avoid accidental overrides |
| `line-height: 0` on Mermaid container | Prevent extra whitespace below SVG |
| `max-width: 100%; height: auto` on Mermaid SVG | Keep diagram responsive |
| Main layout must define explicit TOC width/state behavior | Prevent "class toggles with no visible effect" |
| Focus-visible styles required | Keyboard usability |
| Responsive rules required for mobile TOC | Desktop-only sidebars break mobile usability |

### HTML Structure

```text
.page-shell
  ├── nav.toc
  │     ├── .toc-header
  │     │     ├── h2 "Contents"
  │     │     └── .toc-controls
  │     │           ├── button#themeToggle.toc-btn
  │     │           └── button#tocToggle.toc-btn
  │     └── .toc-body
  │           └── ul > li > a (TOC links)
  └── main.main-content
        ├── section#overview (Hero)
        ├── section#facts (Quick Facts)
        ├── #searchWrap + #noResults
        ├── section#diagram (Mermaid)
        ├── .proof-summary (Verification Summary)
        ├── section#steps (Workflow Steps accordions)
        ├── section#route-outs
        ├── section#terminals
        ├── section#artifacts (Artifact cards)
        └── section#proof (Proof metadata)
```

**Theme toggle placement:** The theme toggle button lives inside the TOC sidebar's header controls (`.toc-controls`), not as a fixed-position element. This avoids fixed-position overlap issues and groups related controls in one place.

**Sidebar close behavior:** When the TOC is hidden, `.main-content` expands to fill the full available width via `max-width: calc(100vw - 4rem)` rather than simply shifting left. The `.page-shell` uses flexbox to achieve this without position:fixed tricks.

### Mermaid CDN (ESM only)

```html
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
</script>
```

Never use local split Mermaid ESM bundles.

### Side Panel / TOC Contract (MANDATORY)

Generated documentation pages with a TOC must implement TOC as a full state/layout system.

#### Required DOM contract

The sidebar and body must start in the **same state**. If the nav has `class="toc collapsed"`, the body must have `class="toc-hidden"`. If the nav has `class="toc"` (open), the body must not have `toc-hidden`. Mismatched initial states cause inverted toggling.

```html
<!-- Option A: Sidebar OPEN by default (default for desktop) -->
<nav class="toc" aria-hidden="false" aria-label="Table of contents">
<body>

<!-- Option B: Sidebar CLOSED by default (default for mobile-first) -->
<nav class="toc collapsed" aria-hidden="true" aria-label="Table of contents">
<body class="toc-hidden">

<button id="tocToggle"
        type="button"
        aria-controls="toc"
        aria-expanded="true"
        title="Toggle table of contents">
  ☰
</button>

<aside id="toc" class="toc" aria-label="Table of contents"></aside>

<main class="main-content"></main>
```

#### Required JS behavior

```javascript
function initTocToggle() {
  const btn = document.getElementById('tocToggle');
  const toc = document.getElementById('toc');
  const isMobile = window.matchMedia('(max-width: 960px)').matches;

  if (!btn || !toc || btn.dataset.bound === 'true') return;
  btn.dataset.bound = 'true';

  // Determine initial state from nav's collapsed class
  const navCollapsed = toc.classList.contains('collapsed');
  const mobileCollapsed = isMobile;

  // Force body class to match initial nav state — this prevents the
  // "toggle inverted" bug where nav and body disagree on initial state.
  // Side-effect of this call: if HTML has nav.collapsed but body has no
  // class, this corrects body before any click handler fires.
  if (navCollapsed || mobileCollapsed) {
    document.body.classList.add('toc-hidden');
  } else {
    document.body.classList.remove('toc-hidden');
  }

  function setTocState(expanded) {
    toc.classList.toggle('collapsed', !expanded);
    document.body.classList.toggle('toc-hidden', !expanded);
    btn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
  }

  setTocState(!isMobile);

  btn.addEventListener('click', () => {
    const expanded = btn.getAttribute('aria-expanded') === 'true';
    setTocState(!expanded);
  });
}
```

**Critical invariant**: Before any click, `nav.classList.contains('collapsed')` must equal `body.classList.contains('toc-hidden')`. If the HTML hardcodes one but not the other, the JS must reconcile them at init time — do not rely on the HTML being perfectly synchronized. The JS must be resilient to a desynchronized initial DOM state.

#### Required CSS behavior

```css
:root { --toc-width: 18rem; }

.page-shell { display: flex; min-height: 100vh; }

.toc { width: var(--toc-width); }
.main-content {
  flex: 1;
  transition: max-width 180ms ease, margin-left 180ms ease;
  max-width: calc(100vw - var(--toc-width) - 4rem);
  margin-left: var(--toc-width);
}
body.toc-hidden .main-content {
  margin-left: 0;
  max-width: calc(100vw - 4rem);  /* expands to fill space on close */
}

@media (min-width: 961px) {
  .toc.collapsed,
  body.toc-hidden .toc {
    transform: translateX(-100%);
    opacity: 0;
    pointer-events: none;
  }
}

@media (max-width: 960px) {
  .toc {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: 1000;
  }

  .toc.collapsed,
  body.toc-hidden .toc {
    transform: translateX(-100%);
    opacity: 0;
    pointer-events: none;
  }
  .main-content { margin-left: 0; max-width: calc(100vw - 4rem); }
}
    transform: translateX(-100%);
    opacity: 0;
    pointer-events: none;
  }

  .main-content { margin-left: 0; }
}
```

### Search UI (MANDATORY)

Artifacts must include client-side search across:

- section titles
- step names
- routing labels
- terminal states
- code/pre blocks where practical

Minimum behavior:
- input field
- incremental filtering/highlighting
- "no results" state
- clear button

### TOC / Section Deep-linking (MANDATORY)

- Every major section must have a stable `id`
- TOC links must target those IDs
- Hash navigation must scroll correctly
- Opening a deep link to a collapsed step must reveal that step

### Reset Button (mandatory)

Every Mermaid diagram with zoom controls must include reset.

### DOMContentLoaded + Module Script Timing

Module scripts are deferred. Initialization order must be explicit and deterministic.

### JS Lifecycle Rules (MANDATORY)

1. Never bind interaction listeners to Mermaid-generated SVG nodes.
2. Always `await mermaid.run()` before querying SVG or applying transforms.
3. Theme rerenders must preserve viewport state.
4. Per-diagram viewport state must live in a stable object keyed by diagram ID.
5. Wheel handlers must use `{ passive: false }`.

### Advanced Viewport Mode (PREFERRED)

Use advanced viewport mode by default for dense or multi-diagram pages.

Expected features:
- drag-to-pan
- cursor-centric wheel zoom
- zoom buttons
- reset
- persistent viewport state across rerenders
- keyboard support where practical

### Testing

Use both DOM assertions and visual verification. Do not rely on class toggles alone as proof that layout works.

Mandatory assertions:
- TOC toggles visible layout state
- TOC links resolve
- Mermaid SVG exists
- zoom/reset change transform as expected
- theme rerender preserves viewport state
- search returns expected hits
- no console errors

---

## Output Requirements

Required:
- `index.html`

Recommended:
- `workflow-model.json`
- `artifact-proof.json`
- `diagram.mmd`
- `diagram.svg`

---

## Integration with skill-craft

skill-craft invokes `/skill-to-page` during EXECUTING when HTML output is needed:

```bash
/skill-to-page <target-skill>
```

The `skill-craft` HTML guidance should be reduced to:

> Delegate all HTML artifact generation to `/skill-to-page`.

This keeps HTML generation centralized, reusable, and verifiable.
