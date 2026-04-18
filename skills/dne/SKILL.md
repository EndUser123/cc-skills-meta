---
name: dne
description: DUF-NSE - Pre-mortem checks + Next Steps. Past to future analysis.
version: "1.0.0"
status: "stable"
category: strategy
triggers:
  - /dne
  - "review and next"
  - "what now"
  - "session summary"
aliases:
  - /dne

suggest:
  - /nse
  - /r
  - /design
  - /llm-brainstorm

execution:
  directive: |
    Perform a "Past → Future" analysis:
    1. DUF (Past): Run pre-mortem checks on recent work. Use conversation history (Read/Edit/Write tool calls in THIS chat) as the sole source of scope. Do NOT run git commands for scope detection. Auto-commit hooks fire on every edit — assume all edits are committed. Check only whether a push occurred in this conversation.
    2. NSE (Future): Propose next steps based on findings.
    3. **Grouping**: Organize action items into Priority (Red), Maintenance (Yellow), and Suggestions (Blue).
    4. **Filtering**: Do NOT list "N/A" or "None" items. Only list actionable items.
    5. **Constraint**: Filter all action items against SoloDevConstitutionalFilter.
  default_args: ""
  examples:
    - "/dne"
    - "/dne --minimal"

do_not:
  - use "lock ordering" or "enterprise-grade" patterns
  - suggest background services or real-time metrics
  - suggest autonomous execution or self-healing
  - require team approval
  - run git status, git log, or any git commands for scope detection (conversation history is the only source)

hooks:
  PostToolUse:
    - matcher: "Skill"
      hooks:
        - type: command
          command: python -c "import sys; sys.exit(0)"
          timeout: 10
---

# DUF-NSE - Past → Future Analysis

## 🤖 Identity: Self-Validating Agent

> [!IMPORTANT]
> You are a **supervised agent**. A validator script runs after every response.
> 1. **Validation is Mandatory**: Your outputs are checked for required sections.
> 2. **Trust the Error**: If you see "VALIDATION ERROR", it is real. Do not argue.
> 3. **Fix and Retry**: Your job is not done until the validator passes.

**Combined workflow:** Run DUF checks on recent work, then propose NSE next steps.

**Philosophy:** "What did I just do?" (DUF) → "Is it safe?" (DUF) → "What's next?" (NSE)

## Purpose

Past-to-future analysis combining DUF cognitive pre-mortem checks with NSE next-step proposals.

## Project Context

### Constitution/Constraints
- Follows CLAUDE.md constitutional principles
- Solo-dev appropriate (Director + AI workforce model)
- All action items filtered against SoloDevConstitutionalFilter
- Evidence-first, verification-required

### Technical Context
- Conversation history (Read/Edit/Write tool calls in THIS chat) is the ONLY source of scope
- No git commands for scope detection — unreliable in multi-terminal environments
- Auto-commit hooks fire on every edit — all edits are assumed committed
- Push state inferred from presence/absence of push commands in conversation
- Constitutional filter: Multi-human collaboration prohibited (AI collaboration appropriate)
- Action items must be specific and informative

### Architecture Alignment
- Integrates with /r and /nse workflows
- Part of CSF NIP governance framework
- Supports session-handoff and /design workflows

## Your Workflow

1. Extract conversation_files: scan this conversation for Read/Edit/Write tool calls → collect touched file paths
2. Infer push state: did a push command (Bash `git push` or `/push` skill) appear in this conversation?
3. Run DUF cognitive checks on conversation_files
4. Generate NSE next steps with constitutional filtering

## Validation Rules

- Conversation history is the ONLY source of scope — no git commands
- All edits are assumed committed (auto-commit hooks fire on every edit)
- Push state inferred from conversation (push command seen → pushed; otherwise → not pushed)
- Action items must state WHAT and WHY
- Filter all actions against SoloDevConstitutionalFilter

### Prohibited Actions

- "lock ordering" or "enterprise-grade" patterns
- Background services or real-time metrics
- Autonomous execution or self-healing
- Requiring team approval
- Relying solely on cached git status

## Constitutional Compliance

**CRITICAL:** All action items MUST be filtered against solo-dev constitutional constraints. See `references/constitutional-filter.md` for prohibited patterns table, Python filter integration, and required filter steps.

## Quick Start

```bash
/dne                    # Full analysis: checks + next steps
/dne --minimal          # Brief output only
```

## Workflow

```
STEP 1: DUF (Past)
    ↓ Check recent changes
    ↓ Run cognitive checks (blast radius, rollback, etc.)
    ↓ Generate action items for any risks found
    ↓ FILTER: Remove constitutional violations
    ↓
STEP 2: NSE (Future)
    ↓ If DUF passes: propose next steps
    ↓ If DUF finds issues: fix first, then next steps
    ↓
OUTPUT: Combined assessment + action items
```

## DUF Phase (Past)

Run these checks on recent changes:

| Check | Purpose |
|-------|---------|
| **Pre-mortem** | What breaks next week? |
| **Blast Radius** | What depends on what changed? |
| **Rollback** | Can I revert this? |
| **Empty Test** | Did I test with null/empty/zero? |
| **Inversion** | What's the easiest way this fails? |

Session scope detection (conversation history only):

```
conversation_files = all file paths from Read/Edit/Write tool calls in THIS conversation
push_seen        = any Bash `git push` or `/push` skill call appears in conversation
```

**Commit state:** Auto-commit hooks fire on every Edit/Write. All edits are committed. Never ask or suggest committing.

**Push state:** Inferred from conversation. No push command seen → not pushed → suggest `d - push`.

See `references/duf-phase.md` for the mandatory execution sequence, git avoidance rationale, and anti-patterns.

## NSE Phase (Future)

Based on DUF results:

| DUF Result | NSE Action |
|------------|------------|
| **Safe** | Propose next steps (commit, push, next task) |
| **Risks found** | Add fix actions before proceeding |
| **Critical issues** | Block progress, fixes required |

## Risk Assessment (Objective Formula)

**Tier × Size × Kind Formula** replaces subjective L×I scoring:

```
risk_score = (tier_weight × 0.5) + (size_weight × 0.3) + (kind_weight × 0.2)
```

**Implementation**: `scripts/risk_calculator.py`

**Components:**
- **Tier** (50% weight): How central is the code?
  - CORE (1.0): Central architecture, critical paths
  - HIGH (0.8): Important subsystems
  - MEDIUM (0.6): Standard features
  - LOW (0.4): Peripheral features
  - UTILITY (0.2): Helper code, tools

- **Size** (30% weight): How much code is changing?
  - LARGE (1.0): Multi-file, extensive changes
  - MEDIUM (0.6): Single file, moderate changes
  - SMALL (0.3): Function-level changes
  - TINY (0.1): Minor tweaks

- **Kind** (20% weight): What type of change?
  - REFACTOR (1.0): Restructuring existing code
  - FEATURE (0.8): Adding new functionality
  - BUGFIX (0.6): Fixing bugs
  - CONFIG (0.3): Configuration changes
  - DOCS (0.1): Documentation only

**Risk Levels:**
- **CRITICAL**: ≥ 0.8 (highest risk)
- **HIGH**: ≥ 0.7
- **MEDIUM**: ≥ 0.5
- **LOW**: < 0.5

**Examples:**
- CORE + LARGE + REFACTOR = 1.0 (CRITICAL) - Major architectural refactoring
- UTILITY + TINY + DOCS = 0.15 (LOW) - Documentation update
- MEDIUM + MEDIUM + FEATURE = 0.64 (MEDIUM) - Standard feature addition

## Output Format

```yaml
## DUF-NSE Analysis: [change description]

**Risk Score:** [0.0-1.0] ([CRITICAL/HIGH/MEDIUM/LOW])
**Checks Run:** [list of checks actually performed]

### Push State
[Pushed / Not yet pushed — inferred from conversation]

### Findings
• Pre-mortem: [one sentence failure scenario]
• Inversion: [one sentence obvious risk]
• Second-Order: [one sentence consequence] - SKIP for Trivial changes
• Red Team: [one sentence attack vector] - SKIP for Trivial/Moderate
• Empty Test: [one sentence edge case to check] - SKIP for Trivial
• Blast Radius: [one sentence dependency impact]
• Observability: [one sentence logging concern] - SKIP for Trivial
• Assumptions: [one sentence unverified belief] - SKIP for Trivial
• Rollback: [one sentence revert strategy]
• Value Reveal: [one sentence upside] - SKIP for Trivial

  ### Action Items

  **🔴 Priority (Critical/Fixes)**
  **1** - [Highest Priority Fix] - [WHY it matters]
  **2** - [Critical Verification] - [WHY it matters]

  **🟡 Maintenance (Cleanup/Tech Debt)**
  **3** - [Cleanup Task] - [WHY]
  **4** - [Tech Debt Item] - [WHY]

  **🔵 Suggestions (Optional)**
  **5** - /design - [Why architectural review is needed]
  **6** - /test - [Why specific testing is needed]
  **7** - [optimization/refactor] - [WHY]

  **⚪ Git Operations**
  **d** - push (include ONLY if no push command was seen in this conversation)

  **x** - all (execute all Priority and Maintenance items)
  **0** - none (skip action items)

  ### Assessment
  [Overall: Safe to proceed / Needs review / High risk]
  [Risk Score: 0.0-1.0] ([CRITICAL/HIGH/MEDIUM/LOW])
  [Tier/Size/Kind breakdown if applicable]
```

## Action Items

**CRITICAL: Action items MUST be specific and informative**

Each action item MUST state:
1. **WHAT** to verify, check, or fix (specific file, function, behavior)
2. **WHY** it matters (what breaks, what risk, what assumption)

**Forbidden patterns (vague, uninformative):**
- "none" - tells nothing about what was done or what to check
- "trivial fix" - doesn't say what was fixed or what to verify
- "cleanup" - doesn't say what was cleaned or why
- "not needed" - doesn't explain why not needed

**Required pattern (specific, informative):**
- "Verify X still works after Y change" - WHAT to verify, WHAT changed
- "Check that Z handles edge case Q" - WHAT to check, WHICH edge case
- "Confirm A doesn't break B" - WHAT to confirm, WHAT depends on it

**Examples:**

| Bad | Good |
|-----|------|
| "none (trivial fix)" | "Verify debug print removal doesn't break scheduler diagnostics" |
| "cleanup" | "Confirm removed conditional doesn't skip subtitle downloads" |
| "not needed" | "/design not needed - single-line change within same function" |

**Action Items Rules:**
- **Group items** by importance (Priority/Maintenance/Suggestions).
- **Omit N/A items**: If a category (e.g. /design) is not needed, do NOT list it.
- **Single-character selection**: Maintain 1-9, a-z selection IDs.
- **x** = Execute all Priority + Maintenance items.
- **0** = Skip all.

## Use When

- **End of session:** Review work before stopping
- **Before commit:** Make sure nothing was forgotten
- **Between tasks:** Reset and plan next steps
- **After significant change:** Full review + forward planning

## CKS Handoff (Knowledge Persistence)

After completing `/dne`, consider running `/cks-store` to persist key findings:

```bash
/cks-store --context "session_summary" --query "..." --confidence 80
```

This enables future sessions to recall patterns, pitfalls, and decisions from this session.
