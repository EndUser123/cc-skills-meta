# Output Format Enforcement

How to make a skill reliably produce a specific output format.

## The Problem

LLM skills often need structured output (RNS format, JSON schemas, numbered action lists, etc.). SKILL.md prose instructions alone are unreliable — the LLM may summarize, reformat, or drift from the spec over a long session.

## Structural Patterns (strongest to weakest)

### 1. Validator Hook (strongest)

A PostToolUse or Stop hook that parses the output and blocks if format is wrong.

**When**: The skill produces machine-readable artifacts (JSON, RNS pipe format, structured files).

**Pattern**:
```python
# Stop hook validates artifact format
machine = artifact.get("machine_output", [])
if not any(l.startswith("RNS|D|") for l in machine):
    errors.append("machine_output missing RNS|D| header")
    # exit(2) blocks the session stop
```

**Example**: `skills/gto/hooks/stop.py` — validates RNS|D| and RNS|Z| markers in artifact JSON.

**Why it works**: Blocking hooks are the only enforcement mechanism that cannot be ignored. The LLM cannot bypass `exit(2)`.

### 2. Reference File + Read Directive

SKILL.md instructs the LLM to read a reference file before rendering output.

**When**: The skill has a canonical format defined in code or a separate spec file.

**Pattern in SKILL.md**:
```
### Step N: Display Results

Read the canonical format spec before rendering:

    Read file: skills/{skill}/__lib/machine_render.py

Use the same domain map, emoji, and numbering when rendering.
```

**Example**: `skills/gto/SKILL.md` Step 4 points to `machine_render.py`.

**Why it works**: The reference file is executable code or a dedicated spec — it's authoritative and single-source. The LLM reads it fresh each invocation, reducing drift.

**Anti-pattern**: Duplicating format rules inline in SKILL.md prose. The LLM treats inline prose as advisory and may not follow it precisely on long sessions.

### 3. Canonical Render Module

A Python module that both produces machine output AND serves as the format spec.

**When**: The skill has executable code that already renders the format.

**Pattern**:
```python
# machine_render.py — both executable AND the spec
DOMAIN_MAP = {"quality": ("🔧", "QUALITY"), ...}

def render_machine_format(findings) -> str:
    """Renders RNS pipe-delimited format. This docstring IS the spec."""
```

**Why it works**: Code can't drift. If the render module changes, the output changes. No prose/code divergence possible.

### 4. Format-Spec Reference File

A dedicated markdown file with the format template and rules.

**When**: No executable render module exists, but the format is complex enough to warrant its own spec.

**Pattern**: `skills/{skill}/references/output-format.md` with:
- Full template with placeholders
- Forbidden patterns (what NOT to do)
- Required fields checklist
- Examples of good vs bad output

**Example**: `skills/dne/references/output-format.md`

### 5. SKILL.md Inline Rules (weakest)

Format rules embedded directly in SKILL.md prose.

**When**: The format is simple (3-5 rules) and the skill is short.

**Limitations**:
- LLM may not follow precisely on long sessions
- No programmatic enforcement
- Duplicates if multiple skills share the same format

**Mitigation**: Keep rules to a concise checklist, not a full template.

## Decision Guide

| Situation | Use |
|-----------|-----|
| Machine-readable output that gets parsed downstream | Validator hook (#1) + Render module (#3) |
| Human-readable but structured (RNS, numbered lists) | Reference file (#2) + Render module (#3) |
| Complex format with forbidden patterns | Format-spec reference (#4) |
| Simple 3-5 rule format | Inline rules (#5) only |
| Format shared across multiple skills | Render module (#3) or format-spec reference (#4) |

## Existing Implementations

| Skill | Pattern | Reference |
|-------|---------|-----------|
| GTO | Validator hook + Render module + Read directive | `skills/gto/hooks/stop.py`, `skills/gto/__lib/machine_render.py` |
| RNS | Format-spec in SKILL.md | `skills/rns/SKILL.md` "Output Format" section |
| Retro | Cross-reference to RNS format | `skills/retro/SKILL.md` "Follow the `/rns` output format exactly" |
| DNE | Format-spec reference file | `skills/dne/references/output-format.md` |

## Checklist for Skill Authors

When a skill needs specific output format:

- [ ] Is the output parsed by downstream tools? → Add validator hook
- [ ] Does a render module already exist? → Point to it, don't duplicate
- [ ] Is the format shared across skills? → Extract to shared reference
- [ ] Are there forbidden patterns? → Document them explicitly
- [ ] Does the SKILL.md point to the format authority (code or spec file)? → Read directive, not inline prose
- [ ] Does the format spec survive SKILL.md edits? → Separate file, not inline
