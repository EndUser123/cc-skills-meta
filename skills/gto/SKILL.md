---
name: gto
version: 3.6.0
status: "stable"
description: Analyze what happened in this session and recommend what to do next. Detects: what skills were used, what wasn't completed, what gaps exist, what other skills should be invoked (like /pre-mortem after code changes, /critique after reviews, /git after edits).
category: analysis
enforcement: strict
triggers:
  - /gto
  - "what gaps do we have"
  - "session health"
  - "analyze project state"
workflow_steps:
  - execute_gto_analysis
allowed_first_tools:
  - Bash
required_first_command_patterns:
  - '^python\s+P:/.claude/skills/gto/gto_orchestrator\.py(?:\s|$)'
required_first_command_hint: Run gto_orchestrator.py first to initialize the session analysis workflow.
---

# GTO v3.1 - Strategic Next-Step Advisor

Reads session history to understand what happened, then recommends what skills to run next.

## What It Does

GTO analyzes your codebase to identify gaps, tasks, and opportunities across:
- Missing test coverage
- Documentation gaps
- Code quality issues (TODO, FIXME, etc.)
- Dependency health
- Project health metrics
- Contract gaps (producer/consumer mismatches, implied schemas, stale-data risks)
- **Chat history patterns** (recurrent issues, cleanup opportunities)

## Completeness Target (v3.x)

"Complete" for GTO v3.x means:

| Layer | Criterion | Target |
|-------|-----------|--------|
| L1 detectors | All 3 transcript-based detectors produce output | 100% |
| L1 detectors | Transcript-based detectors handle missing transcript gracefully | 100% |
| L2 subagent | GapFinderSubagent produces categorized gaps | 100% |
| L2 subagent | No silent failures (unhandled exceptions) | 0 in last 10 runs |
| Output | Health score 0-100% reported | 100% |
| Output | Gap list non-empty (or explicit "no gaps" signal) | 100% |
| Self-verification | gto_assertions.py A1-A5 all pass | 100% |
| Persistence | State file written, readable on next run | 100% |

Scores are measured against this table. A "complete" run is one where all rows are green.
A "partially complete" run is one where 1-2 rows fail. A "failed" run is 3+ failures or a critical (A1/A5) failure.

## Usage

```
/gto
```

GTO auto-detects the target from session context via semantic intent resolution:

1. **Named outputs** (highest priority): If user references a named output from conversation (e.g., "gto on the hook system") → use that
2. **Skill invocation target**: Explicit target from skill args (e.g., `/gto on hooks`)
3. **Active task context**: If `/code` or `/planning` was recently running → the feature/plan they were analyzing
4. **Handoff/RESTORE_CONTEXT**: Stated target from transcript_path links
5. **Recent evidence files**: The system described by the artifact — semantic match, not just recency
6. **Conversation context** (last resort): What was the user working on when GTO was invoked? Weight by intent over timestamps

## Next-Step Integrity Prompts

Before recommending what to do next, `/gto` should run a short internal next-step integrity check:

- What recommendation is being driven by stale artifacts or old session state rather than current evidence?
- What gaps are duplicates, downstream symptoms, or different views of the same root issue?
- What next step would be wrong if the target changed since the last skill run?
- What recommendation is being suggested because the skill is nearby, rather than because it truly owns the gap?
- What follow-up should happen first to prevent wasted work or mis-sequencing?
- What gap still lacks enough evidence to justify a strong recommendation?
- What recommendation would break under multi-terminal state, stale data, or interrupted workflow?
- What should I explicitly not recommend because ownership belongs to `/design`, `/planning`, `/verify`, or another lower skill?
- What would a weaker model over-recommend here as generic cleanup instead of the highest-value next step?
- What recommendation looks helpful locally but would move the workflow away from the real outcome?
- What would change our prioritization if we knew the answers?
- What gap is still a finding or complaint rather than an actionable next step?
- What recommendation is too vague to select and execute without guesswork?
- What dependency, ordering rule, or ownership boundary is still implicit in this gap?
- What action should be split because bundling it would combine unrelated work?
- What severity or effort estimate am I inferring too confidently from weak evidence?
- Have ALL identified gaps been given an explicit disposition (MAPPED, REJECTED with rationale, or DEFERRED with owner+trigger)?
- What should we do next that I have not yet mentioned — what else needs to be done?

These are internal self-check prompts. They are not default user-facing questions and should only surface to the user when `/gto` is genuinely blocked and cannot proceed safely without clarification.

## EXECUTE

**Step 1: Initialize session and terminal isolation**

```bash
# Generate session-scoped identifiers
SESSION_ID="$(uuidgen 2>/dev/null || echo "session-$(date +%s)-$$")"
TERMINAL_ID="${CLAUDE_TERMINAL_ID:-${TERM:-console}-$$}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Platform-safe temp directory
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    TEMP_DIR="${TEMP:-C:/Users/$USER/AppData/Local/Temp}"
else
    TEMP_DIR="${TMPDIR:-/tmp}"
fi

# Terminal-scoped temp subdirectory
TEMP_SUBDIR="$TEMP_DIR/gto-$TERMINAL_ID"
mkdir -p "$TEMP_SUBDIR"

# Evidence directory
EVIDENCE_DIR="P:/.claude/skills/gto/.evidence"
mkdir -p "$EVIDENCE_DIR"
```

**Step 2: Run L1 analysis**

```bash
python P:/.claude/skills/gto/gto_orchestrator.py \
    --format json \
    --output "$TEMP_SUBDIR/gto-l1-$TERMINAL_ID.json" || {
    echo "ERROR: L1 analysis failed"
    exit 1
}
```

**Step 3: Dispatch gap finder and correctness agents via Agent tool (parallel)**

```bash
# NOTE: Agent tool is invoked internally by each subagent
# SKILL.md dispatches; Agent tool handles execution in Claude Code context
# Output paths include terminal_id for multi-terminal isolation

Agent(subagent_type="gap_finder", prompt="Analyze $PROJECT_ROOT for code gaps (TODOs, FIXMEs, XXX, HACK, type: ignore). Scan Python files using Grep for gap patterns. Write findings as JSON to $TEMP_SUBDIR/gto-gap-finder-$TERMINAL_ID.json with format: {\"gaps\": [{\"id\":\"GAP-xxxxxxxx\",\"type\":\"...\",\"message\":\"...\",\"file_path\":\"path/to/file.py\",\"line_number\":N,\"severity\":\"...\"}],\"files_scanned\":N,\"gaps_found\":N}. If no gaps found, write {\"gaps\": [],\"files_scanned\":0,\"gaps_found\":0}.") &

Agent(subagent_type="gto-logic", prompt="Follow the constitution at P:/.claude/CLAUDE.md. Analyze P:/.claude/skills/gto/lib/ for pure logic errors (off-by-one, wrong operators, inverted conditionals). Write findings as JSON to $TEMP_SUBDIR/gto-correctness-logic-$TERMINAL_ID.json with format: {\"findings\": [{\"id\":\"LOGIC-001\",\"severity\":\"HIGH\",\"location\":\"file.py:123\",\"title\":\"...\",\"description\":\"...\",\"evidence\":\"...\"}]}. If no issues found, write {\"findings\": []}.") &

Agent(subagent_type="gto-quality", prompt="Follow the constitution at P:/.claude/CLAUDE.md. Analyze P:/.claude/skills/gto/lib/ for maintainability issues (technical debt, code smells, complex implementations). Write findings as JSON to $TEMP_SUBDIR/gto-correctness-quality-$TERMINAL_ID.json with format: {\"findings\": [{\"id\":\"QUAL-001\",\"severity\":\"MEDIUM\",\"location\":\"file.py:45\",\"title\":\"...\",\"description\":\"...\",\"evidence\":\"...\"}]}. If no issues found, write {\"findings\": []}.") &

Agent(subagent_type="gto-code-critic", prompt="Follow the constitution at P:/.claude/CLAUDE.md. Analyze P:/.claude/skills/gto/lib/ for root cause issues (causal chains, multi-step reasoning failures). Write findings as JSON to $TEMP_SUBDIR/gto-correctness-code-critic-$TERMINAL_ID.json with format: {\"findings\": [{\"id\":\"CAUSE-001\",\"severity\":\"HIGH\",\"location\":\"file.py:78\",\"title\":\"...\",\"description\":\"...\",\"evidence\":\"...\"}]}. If no issues found, write {\"findings\": []}.") &

AGENT_PIDS=($!)
```

**Step 4: Poll for agent completion with early exit**

```bash
TIMEOUT=300
elapsed=0
while [[ $elapsed -lt $TIMEOUT ]]; do
    # Map agent index → output file path (defined once, used each iteration)
    AGENT_OUTPUTS=(
        "$TEMP_SUBDIR/gto-gap-finder-$TERMINAL_ID.json"
        "$TEMP_SUBDIR/gto-correctness-logic-$TERMINAL_ID.json"
        "$TEMP_SUBDIR/gto-correctness-quality-$TERMINAL_ID.json"
        "$TEMP_SUBDIR/gto-correctness-code-critic-$TERMINAL_ID.json"
    )
    # Check each agent: dead PIDs exit fast, live PIDs wait for file
    for i in "${!AGENT_PIDS[@]}"; do
        if ! kill -0 "${AGENT_PIDS[$i]}" 2>/dev/null; then
            wait "${AGENT_PIDS[$i]}" || true
            output_file="${AGENT_OUTPUTS[$i]}"
            if [[ ! -f "$output_file" ]]; then
                echo "ERROR: Agent ${i} died without producing output at $output_file"
                exit 1
            fi
        fi
    done
    # Check if all required output files are present
    if [[ -f "$TEMP_SUBDIR/gto-gap-finder-$TERMINAL_ID.json" ]] && \
       [[ -f "$TEMP_SUBDIR/gto-correctness-logic-$TERMINAL_ID.json" ]] && \
       [[ -f "$TEMP_SUBDIR/gto-correctness-quality-$TERMINAL_ID.json" ]] && \
       [[ -f "$TEMP_SUBDIR/gto-correctness-code-critic-$TERMINAL_ID.json" ]]; then
        echo "All agent output files present after ${elapsed}s"
        for pid in "${AGENT_PIDS[@]}"; do
            wait "$pid" || {
                echo "ERROR: Agent $pid exited with non-zero code"
                exit 1
            }
        done
        break
    fi
    sleep 1
    ((elapsed++))
done

if [[ $elapsed -ge $TIMEOUT ]]; then
    echo "ERROR: Timeout after ${TIMEOUT}s waiting for agents"
    for pid in "${AGENT_PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    exit 1
fi
```

**Step 5: Merge results**

```bash
python P:/.claude/skills/gto/lib/merge_agent_results.py \
    --l1 "$TEMP_SUBDIR/gto-l1-$TERMINAL_ID.json" \
    --gap-finder "$TEMP_SUBDIR/gto-gap-finder-$TERMINAL_ID.json" \
    --agents "$TEMP_SUBDIR/gto-correctness-*-${TERMINAL_ID}.json" \
    --output "$EVIDENCE_DIR/gto-artifact-$SESSION_ID-$TIMESTAMP.json" \
    --validate-schema || {
    echo "ERROR: Merge failed"
    echo "Temp files preserved at: $TEMP_SUBDIR"
    exit 1
}
```

**Step 6: Cleanup with trap protection**

```bash
cleanup() {
    local exit_code=$?
    rm -f "$TEMP_SUBDIR"/gto-*-$TERMINAL_ID.json 2>/dev/null || true
    rmdir "$TEMP_SUBDIR" 2>/dev/null || true
    exit $exit_code
}
trap cleanup EXIT INT TERM
```

**What happens:**
- GTO auto-detects target from session context
- Runs L1 transcript-based detectors (session goal, outcomes, suspicion)
- Dispatches 3 correctness agents in parallel (logic, quality, code-critic)
- Polls for completion, merges results
- Saves JSON artifact to `.evidence/gto-artifact-{session_id}-{timestamp}.json`
- Cleanup via trap ensures temp files removed even on interrupt

## Output

GTO produces:
1. Health score (0-100%) across 4 dimensions
2. Categorized gap list (testing, docs, dependencies, code_quality, contracts)
3. Recommended next steps with effort estimates
4. JSON artifact for tool integration
5. **History insights** (from session transcript analysis)

## Architecture

Three-layer design:
- **Layer 1**: Python deterministic detectors (fast, reliable)
- **Layer 2**: AI subagents (gap finding with line numbers) + Gap-to-Skill Mapper
- **Layer 3**: Claude orchestrator (coordination and formatting)

### Gap-to-Skill Mapping (Layer 2)

GTO includes an intelligent skill recommendation system that analyzes gaps and suggests relevant skills:

**Components:**
- `lib/skill_registry_bridge.py` - Loads skill metadata from registry with fallback catalog
- `lib/gap_skill_mapper.py` - Maps gap types to skill categories using `GAP_TYPE_TO_CATEGORIES`
- `lib/skill_coverage_detector.py` - Gap-aware recommendations for RSN output

**How it works:**
1. When gaps are found, GTO analyzes each gap's type (test_gap, doc_gap, etc.)
2. Gap types are mapped to relevant skill categories (testing, documentation, quality, etc.)
3. Skills are matched based on category, domain, and trigger keywords
4. Recommendations include skill descriptions and rationale

**Gap Type → Skill Category Mapping:**

| Gap Type | Categories | Example Skills |
|----------|------------|----------------|
| test_gap, test_failure | testing, quality | /tdd, /qa, /critique |
| doc_gap, missing_docs | documentation | /doc, /docs, /docs-validate |
| code_quality, design_issue | quality, review | /critique, /uci |
| import_issue, dependency | dependencies | /deps, /verify |
| contract_gap, stale_data_risk, consumer_gap | architecture, verification, state | /design, /planning, /verify |
| git_dirty, uncommitted | vcs, git | /git, /push |
| runtime_error, bug | debugging | /debugRCA, /diagnose |

**LLM Context Injection:**
When generating recommendations, GTO injects skill context into the RSN output so the LLM understands what skills are available and what they do. This enables context-aware suggestions rather than static recommendations.

## Multi-Terminal Safety

Each terminal gets isolated state:
- State directory: `.evidence/gto-state-{terminal_id}/`
- No shared mutable state between terminals
- Atomic writes prevent corruption

## Contract Gap Detection

GTO should detect producer/consumer gaps as a first-class output category.

Examples:

- artifact written but no consumer found
- consumer reads fields never guaranteed by producer
- implied schema exists only in prose/comments
- contract-sensitive boundary exists but no `Contract Authority Packet` exists
- packet exists but downstream work ignores or contradicts it
- no freshness/invalidation rule
- no validator on resume/handoff payload
- stale summary is treated as source of truth over transcript/workspace state

## Routing Behavior

`/gto` should suggest the owning lower skill for each gap family:

- `/design` for state, contract, identity, ordering, dedupe, invalidation, or stale-data gaps
- `/planning` for execution-shape or missing contract-boundary matrix gaps
- `/verify` for unproven behavior or missing boundary-proof gaps
- `/critique` for adversarial review of risky or blind-spot-heavy changes
- `/pre-mortem` for risky fixes, recurring failures, or low-reversibility changes
- `/retro` for process-pattern gaps, repeated issues across sessions, or improvement investigation needs

`/gto` identifies and routes. It does not directly absorb those responsibilities.

## Skill Coverage Log

GTO maintains an append-only log of skill executions per target for routing suggestions.

**Location:** `.evidence/skill_coverage/{target_key}.jsonl`

**Format (one JSON object per line):**
```json
{"skill": "/critique", "target": "skills/usm", "terminal_id": "console_abc123", "timestamp": "2026-03-24T...", "git_sha": "abc1234"}
```

**Key properties:**
- **Append-only**: New entries are always added, never modified
- **Per-target isolation**: Each project/folder gets its own log file
- **No TTL**: Freshness determined by git state — if target changed since last run, coverage is stale
- **Auto-rotation**: Log rotates when >1MB (keeps last 100 entries)

**How it works:**
1. When gaps=0, GTO reads the skill coverage log for the target
2. Checks git state to detect staleness (file changed since skill run)
3. Classifies project type and suggests relevant skills that haven't been run
4. Suggestions appear as RSN findings with `action_type: "Use /skill"`

**Reference:** `lib/skill_coverage_detector.py` — `detect_skill_coverage()` function

## Verification (MANUAL)

**Before claiming "done", you MUST:**

1. Run the binary assertions script:
   ```
   python P:/.claude/skills/gto/evals/gto_assertions.py
   ```
   **Note:** Terminal ID is auto-detected from environment variables (`CLAUDE_TERMINAL_ID`, `TERMINAL_ID`, etc.) or derived from PID+timestamp.

2. Paste the full output showing all assertions passed

3. Only claim "done" if ALL assertions pass (exit code 0, score 100/100)

**If any assertion fails:**
- Diagnose the failure from the assertion output
- Fix the issue (missing artifacts, failed checks, etc.)
- Re-run assertions until all pass
- THEN claim "done"

## Binary Assertions

The assertions script checks 5 criteria:

- **A1**: Artifacts exist (gapfinder, health, or gitcontext files created in last hour)
- **A2**: Health score reported (0-100% in artifact files)
- **A3**: Viability check passed (no FAIL status in viability artifacts)
- **A4**: Git repository valid (.git directory exists)
- **A5**: State directory accessible

## Reference

See `references/` directory for:
- `architecture.md` - Full system architecture
- `api.md` - Complete API reference

**Hook Path Resolution**: GTO skill hooks use relative paths (`../skills/gto/hooks/`) not absolute paths. See `memory/skill_hooks_path_resolution.md` for details on skill-based hook path resolution.

## Recommended Next Steps (RNS)

GTO uses a **dynamic RNS format** that groups findings by category, following the critique RNS pattern but with dynamically-generated domains based on gap types detected.

### Dynamic Domain Categories

The formatter automatically groups gaps into categories based on type:

| Gap Type | Domain | Examples |
|----------|--------|----------|
| `test_failure`, `missing_test` | tests | Failing tests, missing test files |
| `missing_docs`, `outdated_docs` | docs | Missing documentation, outdated docs |
| `git_dirty`, `uncommitted_changes` | git | Uncommitted changes, dirty state |
| `import_error`, `missing_dependency` | dependencies | Import errors, missing packages |
| `code_quality`, `tech_debt` | code_quality | TODO/FIXME, code smells |
| `contract_gap`, `consumer_gap`, `stale_data_risk` | contracts | Missing validators, implied fields, stale-artifact reuse |

### Output Format

🧪 TESTS
  TEST-001 [~5min] [R:1.25] Fix missing test in test_file.py (file:45)

📄 DOCS
  DOC-001 [~15min] [R:1.0] Add docstring to function_x (src/utils.py:78)

🔧 QUALITY
  QUAL-001 [~30min] [R:1.75] Refactor session_manager.py (src/session_manager.py:12)

🐙 GIT
  GIT-001 [~2min] [R:1.0] Commit 3 uncommitted changes in hooks/

### Completeness Check

After executing RNS actions, check whether documentation is stale for the gaps found:

**For each gap type detected**, ask whether related docs are current:
- `test_gap` / `missing_test` → check test coverage in relevant files
- `missing_docs` / `outdated_docs` → update the doc file directly
- `contract_gap` → check if ADR or schema docs need updating
- `code_quality` → check if code comments or inline docs need refresh
- `git_dirty` → commit first, then continue

If implementation happened in a different session from documentation, emit a follow-up DOCS item:
```
📄 DOCS
  [realize/low] DOC-N Update {file} with {specific change}
```

**Rule**: Documentation and implementation in the same session is preferred. If split across sessions, explicitly flag the doc gap.

📦 DEPS
  DEPS-001 [~5min] [R:1.5] Install missing httpx dependency

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

0 — Do ALL Recommended Next Actions (7 items, ~67min total)

**Format rules:**
- Domain sections use emoji headers (🧪 TESTS, 📄 DOCS, etc.) — no markdown fences
- Items use flat global IDs (TEST-001, DOC-001, not hierarchical 1.1, 1.2)
- Each item shows: `[ID] [~effort] [R:reversibility] Description (file:line)`
- Dependency annotations inline: `[causes: ID]`, `[caused-by: ID]`, `[blocks: ID]`
- Priority within domain: critical → high → medium → low
- Ends with `0 — Do ALL Recommended Next Actions` directive

### Fix Verification Mode

After running GTO and executing fixes, verify completeness and edge cases:

1. Collect fix list from GTO artifact or session task list
2. Per-fix: read file, confirm code change present, run tests if they exist
3. Dispatch `adversarial-failure-modes` agent on changed files for edge case analysis
4. Report per-fix: PASS / PARTIAL / FAIL with evidence

**Reference**: `__lib/fix-verification-protocol.md`

**Trigger**: User asks "are all fixes verified?" or "any edge cases?" after GTO run.

### Why Dynamic Domains?

Static RNS sections assume all gap types are always present. GTO detects **which gap types actually exist** in the target project and only generates domains for those types. This prevents empty sections and keeps output focused.

### Prioritization: Use Reversibility

When ranking gaps to fix, apply the Reversibility Scale:

| Score | Action |
|-------|--------|
| 1.0–1.25 (Trivial) | Fix immediately |
| 1.5 (Moderate) | Fix with tests |
| 1.75+ (Hard/Irreversible) | Defer unless critical |

**Reference:**
- `lib/next_steps_formatter.py` — `NextStepsFormatter` class
- `memory/reversibility_scale.md` — Reversibility Scale for decision guidance

## Version

3.6.0 (2026-04-02) - Added Contract Authority Packet gap detection and downstream-consumption checks
3.5.0 (2026-04-02) - Added first-class contract gap detection and routing
3.4.0 (2026-04-01) - Remove --project-root override; rely on session context auto-detection
3.3.0 (2026-03-25) - Intelligent gap-aware skill recommendations with LLM context injection
3.2.0 (2026-03-24) - Added skill coverage append-only log with git-state freshness
3.1.0 (2026-03-22) - Added self-verifying infrastructure with binary assertions
