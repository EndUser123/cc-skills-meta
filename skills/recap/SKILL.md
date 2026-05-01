---
name: recap
description: Catch up on all sessions in this terminal via checkpoint chain traversal and surface unresolved assumptions, contract gaps, Contract Authority Packet gaps, and resume risks
version: 1.5.0
status: stable
category: session
enforcement: strict
triggers:
  - /recap
workflow_steps:
  - execute_recap_workflow
execution:
  directive: Run the recap CLI script to parse transcript files and extract session history, then synthesize findings
  default_args: ""
  examples:
    - "/recap"
    - "/recap brief"
---

# /recap — Terminal-Wide Session Catch-Up

**Problem solved:** "I have 10 sessions compaction-deep in this terminal and I need to know what happened."

## Core Concept

`/recap` aggregates context from ALL sessions in this terminal by walking the full session chain (handoff files + mtime-gap fallback) and parsing each transcript. Session boundaries within each transcript are detected via `sessionId` changes.

`/recap` uses `session_chain.walk_session_chain()` to walk the full session chain via handoff files, then parses each transcript in oldest-to-newest order.

**LLM Executor:** If you are the LLM with full conversation context in memory, skip the transcript search and proceed directly to synthesizing findings from context. Only walk the session chain when resuming a prior session without current context.

1. **Get current session ID**: Extract from `CLAUDE_TRANSCRIPT` env var (stem of the `.jsonl` path), or from `sessionId` field in the transcript file itself
2. **Walk the session chain**: Call `session_chain.walk_session_chain(session_id)` — Strategy 1 uses handoff files (`n_1_transcript_path`), Strategy 2 uses mtime-gap + semantic fallback
3. **Parse each transcript**: Load each transcript path, detect session boundaries via `sessionId` changes, extract goals/message counts
4. **Aggregate context**: Extract goals, message counts from each session
5. **Present summary**: Shows chronological session history

> **`session_chain` module**: `P:/packages/search-research/core/session_chain.py` — exports `walk_session_chain()` (unified entry), `walk_handoff_chain()` (Strategy 1), `walk_sessions_index_chain()` (Strategy 2). All synchronous.

> **Always parse the transcript.** Even when compaction context is available, the transcript contains the authoritative full session chain and detailed working state. Compaction summaries are lossy — they capture goals and outcomes but not the exact sequence of working decisions, errors encountered, or file states mid-edit.

> **⚠️ Fallback behavior**: If `session_chain` import fails, fall back to reading only the current terminal's transcript file directly — it cannot reconstruct the full multi-session terminal history. The synthesis step will have less context to work with.

## Output Structure

The script extracts structured data via regex and presents it in a format compatible with handoff best practices.

### Script Output (aligned with `/handoff` template)
```
# Terminal Recap: {terminal_id}

## Session Metadata
- **Total Sessions**: {count}
- **Terminal ID**: {terminal_id}
- **Current Session**: {session_id}
- **Project**: {project_path}

## Session History

[Session 1] {session_id}
- **Entries**: {n}
- **User messages**: {n} / Assistant messages: {n}
- **Duration**: {duration if available}
- **Goal**: {goal}

### Modified Files
- `{file_path}`
- `{file_path}`

### Original Request
- **User Request**: "{extracted request}"
- **Trigger**: {trigger context}

### Session Objectives
- **Objective 1**: {objective} ({status})
- **Objective 2**: {objective} ({status})

### Final Actions Taken
- **Action A** ({priority})
- **Action B** ({priority})

### Outcomes
- **Outcome 1**: ({status})
- **Outcome 2**: ({status})

### Active Work At Handoff
- **Currently Working On**: {work description}
  - Status: {status}
  - Files Modified: {file_list}
  - Next: {next_step}

### Working Decisions (Critical for Continuity)
- **Decision**: {decision}
  - **Rationale**: {reason}
  - **Impact**: {high|medium|low}

### Current Tasks
- **#{id}**: {task description} ({status}, {priority})

### Known Issues
- **ISSUE-1**: {description} ({status}, {priority})

### Open Questions / Parking Lot
- **Question**: {question text}? ({priority}, {type})
  - *Urgency*: High/Med/Low — what would need to be true to decide this?

### Knowledge Contributions
- **Insight**: {contribution}

### Next Immediate Action
1. {action_1}
2. {action_2}

### Parking Lot (Inversion)
*What would guarantee this session's work fails?* Surface it here.
- **Failure Mode**: {description} — *Mitigation*: {what would prevent it}
- **Assumption**: {core assumption} — *Invalidates*: D# or Action#
- **External Block**: {dependency} — *Blocks*: Action#

### Raw Context
{condensed text for full transcript access}
```
> **⚠️ Note:** The `### Raw Context` section is condensed by `_condense_transcript()` with a 2000-character budget per session. When `### Modified Files` is present, AID distillation replaces Raw Context with AST-level code structure. Content beyond that limit is silently dropped — the structured fields above are the primary evidence source. Full transcript access requires reading the raw transcript file directly.


### Project Context Backdrop

Before synthesizing session narratives, establish project context.

Call `mcp__aid__distill_directory` on the project root with `recursive=false`, `include_implementation=false`. Present the result as a collapsible `## Project Context` section at the top of synthesis. Skip this step for `/recap brief` mode or if the AID MCP tool is unavailable.

### Response Synthesis (LLM task after script output)

When responding to `/recap`, apply reasoning to the script output plus the raw transcript context. For each session, synthesize:

**What happened**: Numbered list of issues. Each item starts with an origin tag in brackets, then describes the issue. Origin tags:
- `[user-reported]` — user explicitly raised this
- `[discovered-during-fix]` — surfaced while working on something else
- `[hook-failure]` — a hook caught or blocked something
- `[skill-escalated]` — a skill routed here from another skill
- `[regression]` — something that worked before broke

Example: `[user-reported] Path refactoring broke imports in cc-skills-meta and claude-chain-miner`

**What was done**: What actually changed (file edits, hooks, skills, configs). Be specific about the actual action.

**In hindsight**: Was the approach right, given what we know now? Only include this section when the fix was a workaround, a detour was taken, or something was missed. Skip it when the fix was straightforward and correct.

**Still pending**: Concrete next steps that were identified but not completed. Each item must be actionable — a command to run, a file to check, or a decision to make. If nothing is pending, omit this section entirely.

**Verification Queue**: For each unverified item, generate a `/tldr-deep` command with the specific function or file name. Prioritize:
- **HIGH**: Blocking items that prevent forward progress
- **MEDIUM**: Code-level verification gaps (untested paths, unverified integration)
- **LOW**: Process-level gaps (documentation, cleanup)

Commands are suggestions only — `/recap` does not execute verification.

Present synthesis as a per-session narrative in the response, not replacing the script output but complementing it.

### Code Structure Enrichment

For sessions with `### Modified Files`, call `mcp__aid__distill_file` on up to 5 files with `include_implementation=false`. The distilled output (function signatures, class hierarchy) serves dual purpose:

1. **Replaces regex-extracted “actions”** with actual function/class changes in synthesis
2. **Replaces `### Raw Context`** with AST-level structure instead of the 2000-char condensed transcript

Regex extraction remains as fallback for sessions without identifiable file changes. Sessions without Modified Files keep the `### Raw Context` fallback.

## Usage

```bash
/recap                    # Show full terminal recap (current + history)
/recap brief              # Show brief catch-up summary only
```

## Routing Behavior

`/recap` uses intent detection to suggest follow-up commands. Map session patterns to the most relevant skill (max 3 suggestions per recap):

| Intent Detected | Follow-Up Command | When to Suggest |
|----------------|-------------------|-----------------|
| Navigation / lost context | `/gto` | Current gaps or stale assumptions are unclear |
| Architecture decisions | `/design` | Unresolved state or contract decisions in prior sessions |
| Complexity hotspots | `/tldr-deep` then `/refactor` | Sessions with many modified files or complex changes |
| Debugging / root cause | `/diagnose` or `/rca` | Sessions with unresolved bugs or error patterns |
| Impact verification | `/verify` | Work discussed or implemented but not actually proven |
| Data flow tracing | `/trace` | Sessions touching data pipelines or state management |

`/pre-mortem` remains the escalation path for sessions with unresolved risk or emergent behavior.

`/recap` should not implement fixes itself.

## Catch-Up Integrity Prompts

Before synthesizing a catch-up summary, `/recap` should run a short internal catch-up integrity check:

- What part of this recap is being inferred from condensed transcript fragments rather than strong evidence?
- What session outcome might be stale, incomplete, or contradicted by later sessions in the same terminal chain?
- What assumption, contract gap, or resume risk is still implicit rather than explicitly surfaced?
- What event in the session chain changed the direction of work, and have I preserved that turning point accurately?
- What recommendation would be misleading if the transcript fallback lost important context?
- What issue was discussed but never actually verified or completed?
- What would a weaker model compress away that materially changes the summary?
- What gap belongs to `/design`, `/planning`, or `/verify` rather than being presented as a local recap observation?
- What summary statement is too confident given the available transcript evidence?
- What would make this recap locally coherent but globally wrong across the full session chain?

These are internal self-check prompts. They are not default user-facing questions and should only surface to the user when `/recap` is genuinely blocked and cannot proceed safely without clarification.

## Implementation Notes

- **Session chain walking**: Uses `session_chain.walk_session_chain()` which first tries handoff-file chain (Strategy 1: `n_1_transcript_path` → prior handoff → ...), then mtime-gap + semantic fallback (Strategy 2)
- Fallback order: handoff files → sessions-index scan → semantic similarity → current transcript only
- Detects session boundaries via `sessionId` field changes within each transcript
- `sessionId` is the stem of the transcript filename (e.g., `8a7b83ff-7d98-47e9-b3b5-3ffabc978c40.jsonl`)
- Semantic extraction (problem/fix/action) via regex against structured output patterns (bugfixes.md format)
- Synthesis (optimal fix reasoning) is performed by the responding LLM — not in preprocessing
