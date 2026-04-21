# PHASE 4.8: Interactive Course (Auto-invoked)

**Objective**: Generate a self-contained HTML course that teaches how the package works.

**When**: Automatically runs after PHASE 4.7 (Media Generation) completes, before PHASE 5 (Portfolio Polish).

**What this does:**
- Analyzes package source code to understand architecture and components
- Generates a standalone HTML course via a 4-pass pipeline, each adding more quality
- Uses the complete codebase-to-course design system (bundled with this skill)
- Outputs to `docs/{package}_course.html` for GitHub Pages hosting

**Required resources** (bundled with this skill — read before generating):

| Resource | Purpose |
|----------|---------|
| `resources/codebase-to-course/design-system.md` | Complete CSS design tokens, typography, animations, module structure |
| `resources/codebase-to-course/interactive-elements.md` | All 17 interactive element patterns with HTML/CSS/JS |

---

### Step 1: Codebase Analysis

Read key source files to understand architecture:
- Core implementation files (`core/*.py`, `*.py`)
- Plugin configuration (`plugin.json`, `hooks.json`)
- Tests to understand expected behavior
- SKILL.md if exists (explains intent)

Extract: actors (main components), data flows, key patterns, the tech stack.

---

### Step 2: Curriculum Design

Structure as 5-7 modules, arc from user-facing behavior → code internals:

| Module | Purpose |
|--------|---------|
| 1 | What this package does + core user action traced into code |
| 2 | Meet the actors — main components and their responsibilities |
| 3 | How the pieces talk — data flow between components |
| 4 | The clever patterns — caching, lazy loading, error handling |
| 5 | When things break — debugging intuition |
| 6 | The big picture — full architecture |

Each module: 3-6 screens, at least one code↔English translation, at least one interactive element from `interactive-elements.md`.

---

### Step 3: Build the Course — 4-Pass Pipeline

Generate `docs/{package}_course.html` in four progressive passes. Each pass adds a quality layer. Read the required resource files before each pass that uses them.

#### Pass 1: Structure & Content

Build the full module/screen skeleton with all text content.

**Output at this stage:**
- Complete `<section class="module">` for each module with correct `id`, `style="background: var(--color-bg or --color-bg-warm)"`
- All `<h1>`, `<h2>`, `<p>` text in every screen
- Nav with dots, progress bar, skip-to-content link
- All code snippets (exact copies from source, syntax-highlighted with Catppuccin classes)
- No interactive elements yet — just structure and text

#### Pass 2: Visual Design System

Read `resources/codebase-to-course/design-system.md` and apply all CSS tokens.

**Add in this pass:**
- Complete `:root` block with ALL design tokens (colors, fonts, spacing, shadows, animations, typography scale)
- Google Fonts `<link>` in `<head>`
- All `.module`, `.module-content`, `.screen` CSS
- Translation block CSS (`grid-template-columns: 1fr 1fr`, `white-space: pre-wrap`)
- Callout boxes CSS, pattern cards CSS, flow diagram CSS, numbered step cards CSS
- Icon-label rows CSS, file tree CSS, permission badges CSS
- Nav, progress bar, scrollbar, atmospheric background CSS
- Accessibility CSS (skip-link, `:focus-visible`, `prefers-reduced-motion`)
- Syntax highlighting for all code blocks
- Bug Prevention Checklist items for Pass 2:
  - [ ] All CSS variable names match design tokens exactly
  - [ ] `prefers-color-scheme` + `prefers-reduced-motion` media queries present
  - [ ] Decorative SVGs have `aria-hidden="true"`
  - [ ] No inline `style=` attributes for color/border on interactive elements
  - [ ] Code blocks: `white-space: pre-wrap`, `word-break: break-word` (no horizontal scroll)

#### Pass 3: Interactive Elements

Read `resources/codebase-to-course/interactive-elements.md` and add all interactive components.

**Add in this pass:**
- Quiz HTML + JS + CSS (`selectOption`, `checkQuiz`, `resetQuiz` functions, `role="radiogroup"`)
- Drag-and-drop matching HTML + JS (mouse + touch)
- Group chat animation HTML + JS (typing indicators, actor colors)
- Message flow / data flow animation HTML + JS
- Interactive architecture diagram HTML
- Layer toggle demo HTML + JS
- "Spot the Bug" challenge HTML + JS
- Scenario quiz HTML + CSS
- Glossary tooltip HTML markup (`<span class="term" data-definition="...">`)
- Bug Prevention Checklist items for Pass 3:
  - [ ] Quiz containers have `role="radiogroup"`, options have `role="radio"`
  - [ ] All interactive elements have keyboard support
  - [ ] Touch support for mobile interactions

#### Pass 4: Polish & Accessibility

Add final quality layer — glossary tooltip JS, scroll animations, keyboard nav, theme toggle.

**Add in this pass:**
- Glossary tooltip JS (position: fixed, appended to body, flip-on-overflow logic — from `interactive-elements.md` Glossary section)
- Scroll-triggered reveal JS (Intersection Observer, `.animate-in` + `.visible` pattern)
- Stagger children JS
- Progress bar JS
- Keyboard navigation JS (arrow keys for module navigation)
- Theme toggle: localStorage-first, `prefers-color-scheme` fallback, `change` listener
- Bug Prevention Checklist final items:
  - [ ] Glossary tooltips use `position: fixed` (appended to body) — never clipped by overflow
  - [ ] `prefers-color-scheme` change listener is wired for mid-session system theme changes
  - [ ] All JS in IIFE with `passive: true` on scroll listeners
  - [ ] `min-height: 100dvh` with `100vh` fallback on modules

---

### Step 4: README Integration

After generating the course HTML, add to README "Additional Media Assets" section:

```markdown
### Interactive Course

[**Learn how {{package_name}} works →**](https://{{github_username}}.github.io/{{package_name}}/docs/{{package_name}}_course.html)

*An interactive walkthrough of the architecture, components, and how everything fits together.*
```

**Auto-skip conditions:**
- User explicitly opts out with `--skip course`
- Package has no source code (e.g., pure documentation package)

**GitHub Pages requirement:**
The course requires GitHub Pages for in-browser viewing. If Pages is not enabled, the README link works as a direct file link to `docs/{package}_course.html` in the repository.

**Duration**: 5-8 minutes (4-pass pipeline ensures maximum quality)

---
