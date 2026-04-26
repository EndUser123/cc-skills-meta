---
name: skill-to-page
version: 1.0.0
description: Transform a skill's SKILL.md into a navigable index.html with mermaid diagrams, TOC, and zoom controls. Replaces scattered HTML-authoring rules in skill-craft.
category: documentation
enforcement: strict
workflow_steps:
  - read_skill_source
  - design_mermaid_diagram
  - mermaid_critic_review
  - generate_html
  - verify_output
triggers:
  - '/skill-to-page'
  - 'create index.html for'
  - 'skill to page'
  - 'document this skill'
argument-hint: <target-skill-name>
context: main
user-invocable: true
depends_on_skills: []
requires_tools: []
aliases: []
status: new
---

# /skill-to-page — Skill to HTML Artifact

Transforms a skill's `SKILL.md` into a self-contained, navigable `index.html` page.

## When to Use

- skill-craft routes here during EXECUTING when HTML output is needed
- Any skill needs a browsable documentation page
- Converting skill documentation to shareable/viewable format

## Input Contract

```bash
/skill-to-page <target-skill-name>
# Example: /skill-to-page go
```

**Reads:** `P:/.claude/skills/{target}/SKILL.md`
**Outputs:** `P:/.claude/skills/{target}/index.html`

---

## Workflow

### Step 1: Read Skill Source

Read the target skill's `SKILL.md` — extract frontmatter, workflow_steps, description, key sections, triggers, hooks.

### Step 2: Design Mermaid Diagram

Design a flowchart representing the skill's workflow or architecture.

**Layout rules:**

| Rule | Why | Enforce with |
|------|-----|--------------|
| **Direction matters** | TD (top-down) keeps phases vertical; LR (left-right) is good for state machines | `flowchart TD` or `flowchart LR` |
| **Group by phase** | Nodes that share a conceptual phase should share a rank | Order nodes so related nodes appear on same rank |
| **Avoid crossing edges** | Crossing lines create cognitive load | If lines cross, swap node order or insert invisible nodes |
| **Color-code edge types** | Different colors let the reader scan intent instantly | Use `stroke` colors; green=forward, red=loop-back, purple=delegation, cyan=data-flow |
| **Curve: basis or monotone** | `curve: 'basis'` gives smooth bezier curves | `flowchart TD with curve: 'basis'` |
| **Padding and spacing** | Nodes too close fuse visually; too far and eye loses thread | `nodeSpacing`, `rankSpacing`, `padding` in flowchart config |
| **Max width** | Wrapped text creates jagged edges | `useMaxWidth: true` on container |

**Node Shape Choices:**

- **Start/End nodes**: `(["label"])` — rounded pill, terminal state
- **Phase headers**: `["Phase 1: DIAGNOSING"]` — plain, just a label
- **Sub-skill nodes**: `"sub-skill-name"` — plain text
- **Conditional nodes**: `{label}` — diamond, decision or branch
- **Data/state nodes**: `[["data label"]]` — rectangle with line break

### Step 3: Mermaid Critic Review (MANDATORY GATE)

Spawn inline agent BEFORE saving any diagram:

```
agent: general-purpose
purpose: Validate mermaid diagrams for clarity, readability, and layout quality
prompt: |
  Review the following mermaid diagram:
  [inject diagram source]
  Check all of:
  1. Trace Start-to-End without lifting your pen
  2. Count edge crossings (flag if > 0)
  3. Verify all node labels are self-explanatory
  4. Verify every non-forward edge has a labeled condition
  5. Check diagram readability at 50% zoom
  6. Check for syntax errors
  Report: { crossings: int, syntax_errors: [], legibility_score: float, issues: [] }
  Gate: crossings == 0 AND syntax_errors == [] AND legibility_score >= 0.8
gate: crossings == 0 AND syntax_errors == [] AND legibility_score >= 0.8
```

**If critic fails:** Fix diagram before proceeding. Common fixes:
- Reorder nodes to eliminate crossings
- Insert invisible nodes to force rank alignment
- Use `rank` directives to group related nodes
- Shorten long labels

### Step 4: Generate HTML

Build `index.html` following HTML authoring rules (see below).

### Step 5: Verify Output

- File exists at target path
- Mermaid renders correctly
- Zoom controls work
- TOC toggle works

---

## HTML Authoring Rules

### CSS Rules

| Rule | Why |
|------|-----|
| No duplicate selectors | Second `.mermaid-container {}` overwrites first — merge all properties into one |
| `line-height: 0` on container | Prevents unwanted vertical space below SVG. Always pair with `overflow-x: auto` |
| `max-width: 100%; height: auto` on SVG | Makes diagram responsive. Never set fixed pixel width on SVG |

### HTML Structure

```
.diagram-wrapper          ← position: relative; overflow: hidden
  ├── .mermaid-container ← line-height: 0; contains <pre class="mermaid">
  └── .zoom-controls      ← position: absolute; bottom/right (sibling, NOT child)
```

**Critical:** `.zoom-controls` must be a sibling of `.mermaid-container`, NOT a child.

Reason: `setTheme()` (and any similar JS that replaces `container.innerHTML`) destroys all descendants. If `.zoom-controls` is inside `.mermaid-container`, zoom buttons vanish on theme toggle.

### Mermaid CDN (ESM only)

```html
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
</script>
```

Never use local ESM bundles — they reference code-splitting chunks (e.g. `chunk-267PNR3T.mjs`) that fail independently. CDN serves the full bundled version correctly.

### TOC Toggle

```javascript
window.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('tocToggle');
  const toc  = document.getElementById('toc');
  if (btn && toc) {
    btn.addEventListener('click', () => {
      toc.classList.toggle('collapsed');
      document.body.classList.toggle('toc-hidden');
    });
  }
});
```

Never use inline `onclick` — causes double-fire with DOMContentLoaded handler: both fire on same click, toggling twice → no net state change.

### Reset Button (mandatory)

Every HTML skill page with a mermaid diagram must include a reset button:

```html
<div class="zoom-controls">
  <button class="zoom-btn" id="zoomIn" title="Zoom in">+</button>
  <button class="zoom-btn" id="zoomOut" title="Zoom out">−</button>
  <button class="zoom-btn zoom-reset" id="zoomReset" title="Reset">1:1</button>
</div>
```

### DOMContentLoaded + Module Script Timing

`<script type="module">` is always deferred — runs **after** `DOMContentLoaded` fires. If TOC init depends on module code having already run, use a different ready signal or move initialization after the import.

### Testing

- **Click testing**: Use native `.click()` in test harnesses — `js("el.click()")` via CDP harness may not dispatch events the same way as a real browser click.
- **Visual verification**: Take screenshots rather than relying on DOM query results when validating that diagrams rendered or toggles worked.

---

## Integration with skill-craft

skill-craft invokes `/skill-to-page` during EXECUTING when HTML output is needed:

```
/skill-to-page <target-skill>
```

**skill-craft update:** The "HTML Artifact Authoring" section becomes:
> *"Delegate to `/skill-to-page` sub-skill for all HTML generation."*

This removes scattered HTML rules from skill-craft and makes index.html generation a first-class, reusable deliverable.