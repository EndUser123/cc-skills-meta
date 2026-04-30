---
name: simplify
description: Simplifies and refines code for clarity, consistency, and maintainability while preserving all functionality. Focuses on recently modified code unless instructed otherwise.
version: 2.0.0
status: stable
category: quality
enforcement: advisory
workflow_steps:
  - identify_changes
  - launch_review_agents
  - fix_issues
triggers:
  - /simplify
---

# Simplify: Code Review and Cleanup

Review all changed files for reuse, quality, and efficiency. Fix any issues found.

## Phase 1: Identify Changes

Run `git diff` (or `git diff HEAD` if there are staged changes) to see what changed. If there are no git changes, review the most recently modified files that the user mentioned or that you edited earlier in this conversation.

## Phase 2: Launch Three Review Agents in Parallel

Use the Agent tool to launch all three agents concurrently in a single message. Pass each agent the full diff so it has the complete context.

### Agent 1: Code Reuse Review

**CRITICAL: Use semantic analysis, not keyword grep.**

For each change:

1. **Determine the pattern type** before searching:
   - Is this a function/variable **DEFINING** behavior? → cross-file search for duplicates
   - Is this a function/variable being **USED**? → check if existing utility already covers it
   - Is this a **MENTION** (reference, not definition)? → skip as duplicate candidate

2. **Cross-file duplicate detection** (not same-file):
   - Only flag duplicates where the SAME PATTERN is actually DEFINED in multiple places
   - Do NOT flag: cross-references, imports, test usage, wrapper functions calling the same utility
   - Do NOT flag: "references pattern" as "defines pattern" — read the code to verify

3. **Cross-domain discrimination**:
   - **Same family** (e.g., two hooks): Cross-reference is legitimate, not duplicate
   - **Different family** (e.g., hook references skill): Verify the pattern is actually duplicated, not just called

4. **Evidence verification**:
   - Before reporting "X files define this pattern", count actual DEFINITIONS via file read (not grep)
   - Keyword matches ≠ definitions — verify with actual code reading
   - If grep finds N matches but only M are definitions (M < N), report M not N

**Duplicate Detection Discrimination Scale:**
| Type | Action |
|------|--------|
| DEFINES | Found another file that also DEFINES this — flag as duplicate |
| MENTIONS | References the pattern without defining it — skip |
| USES_IN_CONTEXT | Calls an existing utility — skip, this is correct usage |
| TEST_USAGE | Test file uses production code — skip |
| CROSS_FAMILY | Hook uses skill utility — skip, cross-family usage is legitimate |

**Verification checklist before reporting:**
- [ ] Read the actual code in matched files (don't trust grep output alone)
- [ ] Count only DEFINITIONS, not mentions or usages
- [ ] Distinguish same-family vs cross-family usage
- [ ] Report: "Found M definitions of pattern X across N files" not "Found N keyword matches"

### Agent 2: Code Quality Review

Review the same changes for hacky patterns:

1. **Redundant state**: state that duplicates existing state, cached values that could be derived, observers/effects that could be direct calls
2. **Parameter sprawl**: adding new parameters to a function instead of generalizing or restructuring existing ones
3. **Copy-paste with slight variation**: near-duplicate code blocks that should be unified with a shared abstraction
4. **Leaky abstractions**: exposing internal details that should be encapsulated, or breaking existing abstraction boundaries
5. **Stringly-typed code**: using raw strings where constants, enums (string unions), or branded types already exist in the codebase
6. **Unnecessary JSX nesting**: wrapper Boxes/elements that add no layout value — check if inner component props (flexShrink, alignItems, etc.) already provide the needed behavior
7. **Nested conditionals**: ternary chains (`a ? x : b ? y : ...`), nested if/else, or nested switch 3+ levels deep — flatten with early returns, guard clauses, a lookup table, or an if/else-if cascade
8. **Unnecessary comments**: comments explaining WHAT the code does (well-named identifiers already do that), narrating the change, or referencing the task/caller — delete; keep only non-obvious WHY (hidden constraints, subtle invariants, workarounds)

### Agent 3: Efficiency Review

Review the same changes for efficiency:

1. **Unnecessary work**: redundant computations, repeated file reads, duplicate network/API calls, N+1 patterns
2. **Missed concurrency**: independent operations run sequentially when they could run in parallel
3. **Hot-path bloat**: new blocking work added to startup or per-request/per-render hot paths
4. **Recurring no-op updates**: state/store updates inside polling loops, intervals, or event handlers that fire unconditionally — add a change-detection guard so downstream consumers aren't notified when nothing changed. Also: if a wrapper function takes an updater/reducer callback, verify it honors same-reference returns (or whatever the "no change" signal is) — otherwise callers' early-return no-ops are silently defeated
5. **Unnecessary existence checks**: pre-checking file/resource existence before operating (TOCTOU anti-pattern) — operate directly and handle the error
6. **Memory**: unbounded data structures, missing cleanup, event listener leaks
7. **Overly broad operations**: reading entire files when only a portion is needed, loading all items when filtering for one

## Phase 3: Fix Issues

Wait for all three agents to complete. Aggregate their findings and fix each issue directly. If a finding is a false positive or not worth addressing, note it and move on — do not argue with the finding, just skip it.

When done, briefly summarize what was fixed (or confirm the code was already clean).
