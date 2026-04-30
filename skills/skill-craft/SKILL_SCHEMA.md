# Skill Frontmatter Schema

Skills declare their execution specifications in YAML frontmatter (between `---` markers) and provide complete context in the body.

---

## Part 1: Frontmatter Schema

```yaml
---
name: skill-name
description: One line description
category: category-name
triggers:
  - /skill-name
  - /alias
  - "phrase trigger"
aliases:
  - /skill-name
  - /alias

suggest:
  - /related-skill-1
  - /related-skill-2

# Execution specification (machine-readable)
execution:
  directive: |
    Brief instruction of what to do when invoked.
    Can be multi-line.
  default_args: ""
  examples:
    - "/skill-name target --flag"
    - "/skill-name . --verbose"

# Prohibited actions (optional)
# REASON: Skills inject execution directives into Claude's context.
# CONSEQUENCE: Descriptive text causes Claude to summarize instead of execute.
do_not:
  - summarize this skill
  - describe what it does
  - use alternative approaches

# Output template (optional - for skills with structured output)
output_template: |
  ## Section 1
  [content]

  ## Section 2
  [content]
---
```

## Part 2: Body Template Structure

After the frontmatter, skills should follow this structure for completeness:

```markdown
# Skill Name

## Purpose
[One-sentence summary of what this skill does]

## Project Context
[Reference relevant project guidelines that constrain this skill's behavior]

### Constitution / Constraints
- [Key principles from CLAUDE.md that apply]
- [Solo-dev or team-specific constraints]
- [Prohibited patterns for this skill]

### Technical Context
- [Relevant tech stack from SPECS.md or project]
- [Integration points to be aware of]

### Architecture Alignment
- [Patterns from ARCHITECTURE.md to follow]
- [Module boundaries to respect]

## Your Workflow
[Numbered steps for how this skill operates]
1. First step
2. Second step
3. ...

## Validation Rules
[Explicit constraints for this skill's operations]
- When [condition]: do [action]
- Before [operation]: verify [requirement]
- After [operation]: check [outcome]

## When to Use
[Triggers or situations where this skill applies]

## Examples
[Concrete usage examples if helpful]

## Integration Points
- [Related skills]
- [Hooks or validators that interact with this skill]
- [Dependencies on other systems]
```

---

## Part 3: Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Skill identifier (used for registry lookup) |
| `description` | Yes | One-line summary |
| `category` | No | Category grouping |
| `triggers` | No | List of trigger phrases/commands |
| `aliases` | No | Alternative command names |
| `suggest` | No | Related skills to suggest |
| `execution.directive` | No | What to execute (fallback: regex extraction) |
| `execution.default_args` | No | Default arguments when none provided |
| `execution.examples` | No | Usage examples |
| `do_not` | No | Prohibited action patterns |
| `output_template` | No | Required output format (for template-based skills) |

### Body Sections

| Section | Required | Purpose |
|---------|----------|---------|
| `## Purpose` | Yes | Clear summary of skill's function |
| `## Project Context` | Recommended | Carries project constraints with skill |
| `## Your Workflow` | Recommended | Step-by-step execution pattern |
| `## Validation Rules` | Recommended | Explicit constraints (beyond `do_not`) |
| `## When to Use` | No | Usage triggers and examples |
| `## Integration Points` | No | Related skills and dependencies |

---

## Part 4: External CLI Documentation Convention

When a skill documents how to invoke an external CLI tool (flags, subcommands, invocation patterns), it MUST:

1. **Include a verification step**: Show the command that confirms the interface (e.g., `tool --help`, `tool --version`, `tool health`).

2. **Annotate with version evidence**: Tag the documented patterns with the version they were verified against:
   `Verified against <tool> v<version> on <date>`

3. **Position the verification step first**: The `--help`/verification check must appear BEFORE the usage patterns, as "Step 0" or equivalent. Models that skip Step 0 are trusting documentation over the live tool.

**Rationale**: External CLI tools evolve independently of this codebase. Documentation written from assumption (rather than from `--help` output) is a hypothesis, not a fact. Weaker models will treat documented patterns as authoritative. This convention forces verification before trust, regardless of model tier.

**Examples of compliant skills**: `ai-groq` (has `health --sanity` verification), `cks` (has `pip show` verification).
**Examples of non-compliant skills**: `ai-models`, `git` skill (have no interface verification step).

---

## Part 5: Evidence-Bound Verification (Anti-Confabulation)

### Problem

Skills that produce freeform summaries create a confabulation surface: the model generates plausible-sounding but unverified claims about file state, line numbers, test results, or config contents. Existing Stop hooks catch this *after* fabrication; this section prevents it *by design*.

### Multi-Terminal Constraint

`git diff` and `git status` show changes from ALL terminals. In a multi-terminal environment, you cannot distinguish "my changes" from "other terminal's changes." Evidence-bound verification must use **session-scoped tool output only** — commands that read specific files or produce deterministic output, not workspace-wide diffs.

### Compaction Resilience

Verification spec lives in skill frontmatter (re-read on skill reload), not in conversation context. After compaction, the skill re-injects the verification requirements when loaded again.

**Verification results are persisted as artifacts** in `P:/.claude/.artifacts/{terminal_id}/{skill_name}/` — the same artifact pattern used by `/refactor` and `/gto`. This means:

- After compaction, session restore can read the artifact file to recover verification state
- The artifact contains timestamps and file hashes, not just PASS/FAIL labels, enabling stale-data detection
- Each terminal writes to its own directory — no cross-terminal pollution

### Frontmatter Extension

Add a `verification` section to skill frontmatter:

```yaml
---
name: my-skill
description: Does things

# ... existing fields ...

# Evidence-bound verification (optional)
verification:
  # Commands to run as the FINAL step before stopping.
  # Each command must produce deterministic, session-scoped output.
  # Do NOT use git diff/git status (multi-terminal pollution).
  commands:
    - description: "Confirm target file exists and has expected content"
      tool: "Read"
      args:
        file_path: "path/to/target.py"
        limit: 10
    - description: "Verify hook registration"
      tool: "Bash"
      args:
        command: "grep -n 'my_hook' P:/.claude/hooks/PreToolUse.py | head -3"
    - description: "Run tests for modified code"
      tool: "Bash"
      args:
        command: "pytest P:/.claude/hooks/tests/test_my_hook.py -v --tb=short 2>&1 | tail -20"

  # Summary format: evidence-only (default) or freeform
  summary_mode: evidence_only

  # Files this skill is expected to modify (for snapshot comparison)
  # Used to detect stale claims after compaction
  expected_artifacts:
    - "P:/.claude/hooks/my_hook.py"
    - "P:/.claude/hooks/tests/test_my_hook.py"
---
```

### Body Section: Verification Step

Skills with `verification` frontmatter MUST include this as their final workflow step:

```markdown
## Step N: Verification (MANDATORY)

You MUST complete this step before stopping. No exceptions.

Do NOT write a freeform summary. Instead:

1. Execute each command from the `verification.commands` frontmatter
2. **Write the results to the artifact file** (see Artifact Persistence below)
3. Paste each tool's output verbatim (last 20 lines for long output)
4. For each command, state one of:
   - PASS: [what the output confirms]
   - FAIL: [what is wrong and what to do next]
5. Add NO interpretive claims not directly supported by the tool output

**Prohibited in summaries:**
- Specific line numbers not shown in this turn's tool output
- File contents not read in this turn
- Test results not from this turn's pytest run
- Claims about "settings.json line 525" without having read that file this turn

**Format:**
```
## Verification Results

### [command 1 description]
[verbatim tool output]
Status: PASS/FAIL — [one sentence]

### [command 2 description]
[verbatim tool output]
Status: PASS/FAIL — [one sentence]
```
```

### Artifact Persistence

Verification results MUST be written to the `.artifacts` directory so they survive compaction:

**Path:** `P:/.claude/.artifacts/{terminal_id}/{skill_name}/verification.json`

**Schema:**
```json
{
  "skill": "my-skill",
  "terminal_id": "console_abc123",
  "session_id": "uuid-here",
  "timestamp": "2026-04-20T16:30:00Z",
  "overall_status": "pass|partial|fail",
  "results": [
    {
      "description": "Confirm target file exists",
      "status": "pass|fail",
      "output_hash": "sha256:abc123...",
      "output_preview": "last 5 lines of tool output",
      "timestamp": "2026-04-20T16:30:01Z"
    }
  ],
  "file_snapshots": {
    "P:/.claude/hooks/my_hook.py": {
      "exists": true,
      "size_bytes": 4096,
      "mtime": "2026-04-20T16:29:55Z",
      "sha256_head": "sha256 of first 4KB"
    }
  }
}
```

**Why `file_snapshots`:** After compaction, session restore can compare current file state against the snapshot. If a file was modified by another terminal after this skill ran, the snapshot detects the mismatch (stale data immunity) without using `git diff`.

**Compaction recovery:** When a session resumes after compaction:
1. Read `P:/.claude/.artifacts/{terminal_id}/{skill_name}/verification.json`
2. For each `file_snapshots` entry, check if current file matches snapshot
3. If mismatch: flag as stale, re-run verification commands
4. If match: trust the artifact — no re-run needed

### `summary_mode` Values

| Mode | Behavior | When to Use |
|------|----------|-------------|
| `evidence_only` (default) | Must paste tool output verbatim. No freeform prose. | Skills that modify files, run tests, or change state |
| `freeform` | Normal summary allowed. Existing claim-verification hooks still apply. | Knowledge-only skills, read-only analysis |

### `expected_artifacts` Purpose

Lists files the skill intends to create or modify. After compaction, a session restore can:

1. Check which artifacts exist
2. Compare against what was claimed in the pre-compaction context
3. Flag stale claims ("the summary says test_my_hook.py was created but it doesn't exist")

This does NOT use git diff — it reads files directly, avoiding multi-terminal pollution.

### Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `verification.commands` | Yes (if `verification` present) | List of tool calls for evidence-bound final step |
| `verification.commands[].description` | Yes | What this command verifies |
| `verification.commands[].tool` | Yes | Tool name (Read, Bash, Grep, Glob) |
| `verification.commands[].args` | Yes | Tool arguments |
| `verification.summary_mode` | No | `evidence_only` (default) or `freeform` |
| `verification.expected_artifacts` | No | Files this skill creates/modifies |

### Why This Works With Existing Infrastructure

- **Stop hooks** (`unified_claim_verifier.py`, `StopHook_cross_validator.py`) still run as backstop
- **Claim patterns** (`__lib/claim_patterns.py`) still catch any fabricated claims that slip through
- **This template** prevents the need for those hooks by structurally eliminating freeform summary generation
- No new hooks required — this is a skill-authoring convention enforced by the skill's own workflow steps

### Example: /tdd Skill

```yaml
verification:
  commands:
    - description: "Confirm test file exists"
      tool: "Bash"
      args:
        command: "ls -la P:/.claude/hooks/tests/test_my_hook.py"
    - description: "Confirm implementation file exists"
      tool: "Bash"
      args:
        command: "ls -la P:/.claude/hooks/my_hook.py"
    - description: "Run tests"
      tool: "Bash"
      args:
        command: "pytest P:/.claude/hooks/tests/test_my_hook.py -v --tb=short 2>&1 | tail -20"
    - description: "Verify hook is registered in dispatch chain"
      tool: "Bash"
      args:
        command: "grep -n 'my_hook' P:/.claude/hooks/PreToolUse.py | head -3"
  summary_mode: evidence_only
  expected_artifacts:
    - "P:/.claude/hooks/my_hook.py"
    - "P:/.claude/hooks/tests/test_my_hook.py"
```
