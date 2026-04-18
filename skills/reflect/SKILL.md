---
name: reflect
description: >
  Analyzes conversation transcripts to extract user corrections, patterns, and preferences,
  then proposes skill improvements. Use this skill when users provide corrections, express
  preferences about code style, or when patterns emerge from successful approaches. Can be
  triggered manually with /reflect or automatically at session end when enabled.
version: 1.2.0
status: beta
category: learning
enforcement: advisory
---

# Reflect - Self-Improving Skills

## Overview

This skill enables Claude Code to learn from conversations by analyzing corrections,
approvals, and patterns, then proposing updates to relevant skills. It implements
a "correct once, never again" learning system.

**Three modes:**
1. **Manual Reflection** — `/reflect [skill-name]` anytime
2. **Automatic Reflection** — Runs at session end via Stop hook (always-on, background)
3. **Queue Processing** — Review accumulated signals from multiple sessions

**Pre-Mortem Analysis:** Detects conversation issues (vague requirements, contradictions,
missing error handling) before they become problems. Runs automatically during reflection.

**Kill Criteria Enforcement (Task #2295):** On each run, checks `sessions.json` for pre-mortem sessions older than 30 days that lack validation timestamps. Displays pending sessions with age and emits advisory about sunk-cost risk. Critically, also extracts HIGH/MEDIUM items from those sessions' `p3.md` files as `critique_lesson` signals — Domain 7a — and stores them to CKS alongside skill-correction lessons.

Reflection should also capture reusable contract-failure lessons such as:
- implied field dependency
- producer-only verification
- stale artifact reused as truth
- missing consumer validator
- compact/resume assumption failure

## Usage Modes

### 1. Manual Reflection (/reflect)
Trigger analysis of the current conversation:
```
/reflect [skill-name]
```
- Without skill-name: Analyzes all skills used in conversation
- With skill-name: Focuses on specific skill

### 2. Automatic Reflection (Stop Hook)
Always-on: Runs automatically at session end via `scripts/hook-stop.sh`.
Early exit if no learning signals found. Runs in background (non-blocking).
Lock file prevents concurrent runs. Logged to `~/.claude/reflect-hook.log`.

### 3. Queue Processing
Accumulated signals from multiple sessions can be reviewed together:
```
/reflect  (no transcript - reads accumulated signals)
```

## Confidence Levels

**HIGH** - Explicit corrections:
- User contradicts Claude's approach with specific alternative
- Pattern: "Don't do X, do Y instead"
- Action: Direct updates with deprecation warnings

**MEDIUM** - Approvals and implicit learning:
- User approves specific approach
- Pattern succeeds multiple times
- Claude discovers pattern through trial and error (retry patterns, tool discovery)
- Action: Add to "Best Practices" or "Discovered Patterns" section

**LOW** - Observations:
- User questions or suggests alternatives
- Pattern: "Have you considered..." or "Why not try..."
- Action: Add to "Considerations" section

## Workflow

1. **Signal Detection** - Scan transcript for corrections/patterns
2. **Context Analysis** - Extract 5-message context around signals
3. **Skill Mapping** - Match signals to relevant skills
4. **Implicit Pattern Detection** (optional) - Detect retry patterns and tool discovery
5. **Pre-Mortem Analysis** - Conversation checks (vague requirements, contradictions, missing error handling)
6. **Change Proposal** - Generate diff of proposed updates
7. **User Review** - Interactive approval with natural language editing
8. **Application** - Safe YAML/markdown updates with backups
9. **Git Commit** - Automatic commit with descriptive message

When a failure involved producer/consumer mismatch, reflection should record both:

- the missing contract element
- the skill or phase where that contract should have been enforced

## Reflection-Upgrade Prompts

Before proposing skill updates, `/reflect` should run a short internal reflection-upgrade check:

- What correction or preference here is a one-off local preference rather than a durable skill improvement?
- What proposal is being driven by a stale or later-overturned part of the conversation?
- What lesson should be pushed into a validator, hook, or test instead of staying as prose?
- What proposed update would overfit the skill to one session and make it worse in general?
- What evidence shows that this pattern is recurring enough to justify changing a skill?
- What ownership boundary is wrong if I change this skill instead of another one?
- What would a weaker model promote as a rule even though it is really an exception?
- What change here reduces one failure mode but creates strategy drift or mechanism leakage?
- What part of the transcript is correction signal versus exploration noise?
- What would make this reflection artifact sound smart but teach the wrong habit?

These are internal self-check prompts. They are not default user-facing questions and should only surface to the user when `/reflect` is genuinely blocked and cannot proceed safely without clarification.

## Emerge, Graduate, And Trace

`/reflect` should use three internal helper passes:

- `emerge`: identify latent patterns across corrections, approvals, and repeated failures that have not yet been articulated clearly
- `graduate`: promote repeated reflection lessons into durable updates such as validator, hook, test, or workflow changes
- `trace`: reconstruct how a correction or preference evolved across the conversation when the final lesson depends on sequence, reversal, or context shift

Use `emerge` when several signals look related but the underlying lesson is still fuzzy.
Use `graduate` when a lesson has enough recurrence and evidence to justify promotion into durable enforcement.
Use `trace` when a proposed change depends on what changed over time rather than on a single isolated correction.

Reference: `P:/.claude/skills/__lib/sdlc_internal_modes.md`

## Routing Behavior

`/reflect` may suggest:

- `/arch` if the repeated lesson is architectural contract ambiguity
- `/planning` if the repeated lesson is missing contract matrix or readiness shape
- `/verify` if the repeated lesson is lack of proof or producer-only verification

`/reflect` captures lessons; it does not rewrite active implementation work by itself.

## Scripts

### Core Engine
- `scripts/reflect.py` - Main orchestration logic (queue checking, pre-mortem, CKS storage, history scanning)
- `scripts/extract_signals.py` - Pattern detection engine (regex + semantic, 4-phase)
- `scripts/update_skill.py` - Safe skill file updates with backups
- `scripts/present_review.py` - Interactive review interface

### Signal Detection
- `scripts/semantic_detector.py` - AI-powered semantic pattern detection
- `scripts/workflow_assumptions.py` - Root cause pattern detection (external tool verification, exit conditions)
- `scripts/tool_error_extractor.py` - Tool error pattern detection

### Implicit Learning
- `scripts/implicit_patterns.py` - Retry patterns, tool discovery, pattern emergence detection
- `scripts/semantic_validator.py` - AI validation of regex-detected signals

### Cross-Skill Learning
- `scripts/learning_ledger.py` - SQLite ledger for cross-repo tracking
- `scripts/scope_analyzer.py` - Project vs global learning scope
- `scripts/promote_learning.py` - Promotion to global CLAUDE.md
- `scripts/multi_target_sync.py` - Multi-repository synchronization
- `scripts/meta_learning.py` - Cross-repository pattern aggregation

### Pre-Mortem Analysis
- `scripts/premortem.py` - Pre-mortem conversation checks (7 checks, phase detection)

#### Meta-Pattern: Self-Verification
See `references/meta-patterns.md` for self-verification pattern details and examples.

### Queue & Accumulation
- `scripts/show_queue.py` - Display pending learnings in review table (sorted by confidence)
- `scripts/accumulate_signals.py` - Multi-session signal accumulation

### Discovery
- `scripts/skill_discovery.py` - Skill finder and matcher

### Quality Validation
- `scripts/validate_pattern_coverage.py` - Pattern coverage validation

### Automation
- `scripts/hook-stop.sh` / `hook-stop.ps1` / `hook-stop.bat` - Stop hook integration (always-on mode)
- `scripts/toggle-on.sh` - Enable auto-reflection
- `scripts/toggle-off.sh` - Disable auto-reflection
- `scripts/toggle-status.sh` - Show status

### CKS Integration
- `scripts/cks_schema_mapper.py` - CKS finding type classification
- `scripts/cks_auto_save.py` - Auto-save module with graceful failure

## Safety Features

- Timestamped backups before all edits
- YAML validation before writing
- Lock files prevent concurrent runs
- Graceful error handling with rollback
- Git status checks before commits

## CLI Options & Monitoring

See `references/cli-options.md` for extract_signals.py flags, environment variables, and production monitoring details.

## Output Format

**CRITICAL**: All reflection reports MUST follow the exact format in `references/output-template.md`.

1. Read the template: `references/output-template.md`
2. Fill in each section using the exact structure shown
3. Include ALL sections even if empty (use provided placeholders)
4. **END WITH "RECOMMENDED NEXT STEPS"** using GTO format (domain-numbered actions with evidence citations)

Each action MUST cite evidence (file:line or Finding ID). This matches GTO skill's evidence-based format.

## CKS Schema Integration

See `references/cks-integration.md` for finding types (PATTERN/REFACTOR/DEBT/DOC/OPT), metadata schema, category mapping, and auto-save workflow.

## References

- **`references/output-template.md`**: Exact output format for all reflection reports (MANDATORY)
- **`references/signal-patterns.md`**: Detailed pattern library for signal detection
- **`references/cli-options.md`**: CLI flags, environment variables, production monitoring
- **`references/cks-integration.md`**: CKS schema, finding types, category mapping, auto-save workflow
- **`references/meta-patterns.md`**: Self-verification pattern and examples
