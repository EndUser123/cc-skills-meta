---
name: config-audit
description: Audit Claude Code configuration artifacts (hooks, skills, CLAUDE.md, agents) for over-engineering, redundancy, and token waste. Uses model routing (haiku for research, sonnet for analysis) with decision memory.
enforcement: advisory
triggers:
  - /config-audit
workflow_steps:
  - discover
  - research
  - analyze
  - synthesize
  - apply_decisions
---

# /config-audit — Configuration Artifact Auditor

Audit Claude Code configuration artifacts (hooks, skills, CLAUDE.md, agents, MCP configs) for over-engineering, redundancy, and token waste. Uses model routing (haiku for research → sonnet for analysis) with decision memory.

## Core Model Routing Pattern

**Phase 1: Research** (runs on haiku — fast/cheap for doc fetching)
- Fetch expert knowledge from official Anthropic docs
- Build rubric for target type
- Memory-backed (faster on repeat runs)

**Phase 2: Analysis** (runs on sonnet — consistent quality for config analysis)
- Apply rubric to target artifact
- Score over-engineering, redundancy, conflicts
- Quote specific evidence with file:line

**Why**: Research is IO-bound (doc fetching), Analysis is CPU-bound (pattern matching). Routing each to the right model reduces cost and improves quality.

## Target Types & Rubrics

### Skills Rubric

**Hook-enforced fields** (only include if needed):
- `enforcement` — REQUIRED: must be `none`, `advisory`, or `strict` (defaults to `strict` if omitted)
- `required_tools` — enables tool gating
- `depends_on_skills` — enables dependency validation
- `workflow_steps` — enables Layer 0 step enforcement
- `triggers` — enables slash command registration
- `suggest` — enables integration validation

**Inert fields** (never include — no hook reads them):
- `context` — no hook validates this
- `user-invocable` — no hook validates this
- `argument-hint` — no hook validates this
- `status` — no hook validates `active`/`inactive`
- `aliases` — no hook validates this
- `category` — no hook validates this

**Minimum valid frontmatter**:
```yaml
---
name: my-skill
description: One-line purpose
---
```

**Token savings**: Removing inert fields saves ~15-40 tokens per skill.

| Target Type | Over-Engine Risk | Key Signals |
|-------------|-----------------|-------------|
| Hooks | Verbose patterns, redundant validation | Pre-check loops, redundant success checks, over-specified timeouts |
| Skills | Inert frontmatter fields, redundant sections | Duplicate workflow_steps, cross-ref instead of integrate, verbose frontmatter |
| CLAUDE.md | Restated built-ins, verbosity | "always read files", "use git", "write clean code" |
| Agents | Tool sprawl, duplicate logic | Over-broad allowed-tools, redundant subagent patterns |

### Over-Engineering Scoring Guide

For each instruction/pattern, score:

1. **Would Claude do this anyway?** → Restated built-in (-10 pts)
2. **Is this project-specific?** → Scope creep if general programming (penalize)
3. **Could this be shorter?** → Verbosity has token cost (penalize)
4. **Does this conflict with another instruction?** → Conflicts (-15 pts)
5. **Is this embedding content that could be referenced?** → Embed → reference (-5 pts)

### Token Budget Tracking

Estimate always-loaded vs on-demand tokens:
- Skills with verbose frontmatter = always-loaded waste
- Hooks with verbose logging = always-loaded overhead
- Large CLAUDE.md files = always-loaded bloat

Report: "Estimated waste: ~X tokens always-loaded"

## Decision Memory

Stores user decisions in `.claude/.config-audit/decisions.json`:

```json
{
  "hook:auth_gate:restated_success_check": {
    "decision": "rejected",
    "reason": "Auth hooks need explicit success validation",
    "timestamp": "2026-04-29",
    "artifact_version": "1.2.0"
  }
}
```

**Key format**: `{type}:{artifact}:{issue_pattern}`

**Staleness detection**: Flag decisions for re-evaluation when:
- Artifact version changes
- 90 days pass
- Claude Code updates change default behavior

## Workflow

### Phase 1: Discover
Discover all target artifacts in scope:
```bash
# For hooks
find .claude/hooks -name "*.py" -o -name "*.md"
# For skills
find .claude/skills -name "SKILL.md"
# For CLAUDE.md
find . -maxdepth 3 -name "CLAUDE.md" -o -name "CLAUDE.local.md"
```

Build configuration map with file paths, line counts, last-modified.

### Phase 2: Research (haiku)
Fetch Anthropic docs for target type:
1. Model Configuration docs
2. Best Practices
3. CLI Reference

Check memory for cached findings first — update only if changed.

### Phase 3: Analyze (sonnet)
For each artifact:
1. Read file
2. Apply rubric based on type
3. Score against over-engineering criteria
4. Quote specific findings with file:line
5. Check against decision memory (annotate, don't suppress)

### Phase 4: Synthesize
Aggregate findings:
- Cross-file duplication (same pattern in multiple files)
- Cross-type redundancy (hook does what skill already does)
- Conflicts (A says X, B says not-X)
- Token waste estimates

### Phase 5: Apply Decisions
Present findings grouped by:
1. **High-impact**: >50 token savings or conflict resolution
2. **Medium-impact**: 20-50 token savings
3. **Low-impact**: <20 token savings, style suggestions

User selects which to apply. Track decisions in memory.

## Output Format

```
CONFIG-AUDIT REPORT
Target: {scope}
Token Estimate: ~{n} tokens always-loaded

### Over-Engineering Findings
[{severity}] {file}:{line} — {pattern}
  Quote: "{evidence}"
  Impact: ~{n} tokens wasted

### Cross-File Duplication
{pattern} defined in {n} files:
  - {file1}
  - {file2}
  Recommendation: {unification or reference}

### Conflicts
{file1} says X but {file2} says not-X

### Token Waste Summary
- Verbosity: ~{n} tokens
- Duplication: ~{n} tokens
- Conflicts: ~{n} tokens
Total estimated waste: ~{n} tokens always-loaded

### Decision Memory
[PASS] {pattern} — previously accepted (2026-04-15)
[REJECT] {pattern} — previously rejected: {reason}
[STALE] {pattern} — decision from {date}, re-evaluate recommended

### Recommendations
1. [High] {action} — saves ~{n} tokens
2. [Medium] {action} — saves ~{n} tokens
...
```

## Agents

### research-config (haiku)
Fetches Anthropic docs, builds target-type rubric, checks memory.

### analyze-config (sonnet)
Applies rubric to artifacts, scores patterns, quotes evidence.

## Integration

Use `/config-audit hooks` to audit hooks
Use `/config-audit skills` to audit skills
Use `/config-audit CLAUDE.md` to audit instruction files
Use `/config-audit agents` to audit agent definitions
Use `/config-audit` (no args) to audit everything in scope

## Not for

- Code quality (use `/sqa` or `/simplify`)
- Architecture decisions (use `/design`)
- Security scanning (use security-focused tools)