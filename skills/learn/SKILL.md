---
name: learn
description: Intelligent lesson capture with novelty detection and usefulness filtering
version: 1.0.0
status: stable
category: learning
triggers:
  - /learn
aliases:
  - /learn
suggest:
  - /review
  - /lessons
  - /cooldown
depends_on_skills: []
workflow_steps:
  - extract_candidates: Extract lesson-worthy segments from session transcript using signal patterns (causal connectors, root causes, decisions)
  - novelty_detection: Query CKS via daemon to check what's already known, assign novelty scores
  - usefulness_scoring: Score candidates by 4 dimensions (novelty, complexity, pattern, impact), total 0-8 scale
  - threshold_filtering: Store only lessons meeting threshold (score ≥ 4), skip low-value noise
enforcement: advisory
---

# `/learn` - Intelligent Lesson Capture

**Adaptive lesson extraction that figures out what you actually learned.**

## Purpose

Extract valuable lessons from your session using:
1. **Pattern detection** - Finds causal connectors, root causes, decisions
2. **Novelty checking** - Queries CKS to avoid duplicates
3. **Usefulness scoring** - Filters by complexity, pattern, impact
4. **Adaptive output** - Shows what matters, skips noise

## Project Context

### Constitution/Constraints
- Evidence-based only (what actually happened in session)
- No speculation or future predictions
- Solo-dev optimized (automatic, minimal friction)

### Technical Context
- **Extractor**: `$CLAUDE_PROJECT_DIR/.claude/skills/learn/lesson_extractor.py`
- **Pipeline**: extract → novelty → score → filter
- **Threshold**: Score ≥ 4 to store
- **Daemon**: Uses semantic search for novelty detection (stubbed in self-contained mode)

### Architecture Alignment
- Replaces `/rr`, `/retro`, `/cooldown` with single smart command
- Integrates with CKS for novelty detection
- Auto-stores high-value lessons

## Your Workflow

```
/learn
→ Analyzing session...
→ Session: 47 min, 3 files changed, 1 bug fixed
→ Checking CKS for existing knowledge...
→ Found 2 new patterns
→ Stored to CKS: pattern_abc123, pattern_def456

✅ Learned 2 new lessons:
1. Terminal detection path mismatch (score: 7)
2. Session isolation via ConsoleHost handle (score: 6)
```

## How It Works

### Stage 1: Extract Candidates

Finds lesson-worthy segments using signal patterns:

| Signal Pattern | Example |
|----------------|---------|
| Causal connectors | "because", "due to", "the reason" |
| Root cause format | "Root cause: X" |
| Problem-solution | "The issue was X, so I did Y" |
| Explicit learning | "I learned that", "discovered" |
| Decision markers | "decided to", "chose X over Y" |
| Investigation | "debugged", "traced", "investigated" |

**Filters out** (noise):
- Routine operations: "ran pytest", "checked git"
- One-off fixes: "fixed typo on line 42"
- Facts/outputs: "created 5 docs"
- Obvious statements: "read the file"

### Stage 2: Novelty Detection

Queries CKS via daemon to check what's already known:

```
Candidate: "SessionStart writes to %TEMP% but skill_execution_state reads from wrong path"
CKS Query: "terminal detection path mismatch"
Result: NOT FOUND → novelty_score = 2
```

```
Candidate: "Caching reduces API calls"
CKS Query: "caching api calls"
Result: FOUND (0.92 similarity) → novelty_score = 0
```

### Stage 3: Usefulness Scoring

Scores each candidate by 4 dimensions (0-2 each):

| Dimension | Score 2 | Score 1 | Score 0 |
|-----------|---------|---------|---------|
| **Novelty** | New to CKS | Partial match | Already in CKS |
| **Complexity** | RCA/investigation | Non-obvious | Obvious |
| **Pattern** | Repeatable | Possible pattern | One-off |
| **Impact** | Architectural | Saves time | Minor |

**Total score = sum of all dimensions (0-8)**
**Threshold: 4+ to store**

### Stage 4: Threshold Filtering

Only stores lessons that meet the threshold:

```
Score 7: "Terminal detection path mismatch" → STORE
Score 6: "Session isolation via ConsoleHost" → STORE
Score 3: "Ran pytest to verify" → SKIP (too obvious)
Score 2: "Fixed typo in config" → SKIP (one-off, low impact)
```

## Validation Rules

### Quality Filter

**What IS a lesson**:
- Non-obvious implementation details
- Patterns that change future behavior
- Root causes requiring investigation
- Decisions with trade-offs

**What is NOT a lesson**:
- Routine operations ("ran pytest")
- One-off fixes ("fixed typo")
- Temporary observations
- Obvious facts

### Evidence-Based Only

- Cite actual session work
- Reference real problems solved
- No speculation about future issues

## Lesson-Quality Prompts

Before storing or skipping a lesson, `/learn` should run a short internal lesson-quality check:

- What candidate here is merely an event, output, or routine operation rather than a reusable lesson?
- What lesson sounds novel locally but is already known, obvious, or too one-off to keep?
- What pattern would stop being true if the surrounding context or constraints changed?
- What score am I inflating because the wording sounds important, not because the lesson is durable?
- What causal claim is being made without enough evidence from the actual session?
- What lesson is really a symptom of a deeper pattern that should be captured instead?
- What would a weaker model over-store here as noisy trivia?
- What lesson should be merged with another because they are the same underlying pattern?
- What lesson is useful only for this repo or session and should not be promoted more broadly?
- What would make this stored lesson teach the wrong habit next time?

These are internal self-check prompts. They are not default user-facing questions and should only surface to the user when `/learn` is genuinely blocked and cannot proceed safely without clarification.

## Emerge And Graduate Passes

`/learn` should use two internal helper passes when extracting lessons:

- `emerge`: identify latent repeated patterns across candidate lessons when the underlying theme has not yet been named explicitly
- `graduate`: decide when a repeated lesson is strong enough to promote into a durable artifact, broader pattern, or stronger enforcement recommendation

Use `emerge` when several candidates look related but the shared lesson is still unclear.
Use `graduate` when the same underlying lesson keeps reappearing and should stop living as isolated session trivia.

Reference: `P:/.claude/skills/__lib/sdlc_internal_modes.md`

## Output Format

### When Lessons Found

```
/learn

→ Analyzing session (23 min, 3 files, 1 bug fix)
→ Checking CKS for: terminal, detection, path, mismatch
→ Result: 2 new patterns found

✅ Learned 2 new lessons:

1. [score: 7] Terminal detection path mismatch
   SessionStart writes to %TEMP%/claude_terminal_id.txt but
   skill_execution_state reads from P:/.claude/state/ (wrong path)
   → CKS: pattern_abc123

2. [score: 6] Session isolation via ConsoleHost handle
   ConsoleHost handle provides unique terminal ID across all
   PowerShell sessions, more reliable than PID-based detection
   → CKS: pattern_def456
```

### When Nothing New

```
/learn

→ Analyzing session (5 min, 2 config edits)
→ Checking CKS for: config, settings
→ Result: Routine changes, no new patterns

✅ Nothing new to learn (routine maintenance)
```

### When Everything Already Known

```
/learn

→ Analyzing session (15 min, path fix)
→ Checking CKS for: path, detection
→ Result: Pattern already in CKS (pattern_abc123)
→ Summary: Fixed another instance of known issue

ℹ️ Pattern already known, nothing new to store
```

## Usage

```bash
/learn                                    # Extract from transcript (auto-detect)
/learn "Lesson text - category"          # Store direct lesson (positional)
/learn --lesson "Lesson text - category" # Store direct lesson (explicit flag)
/learn --verbose                         # Show full scoring breakdown
/learn --dry-run                         # Show what would be stored
```

### Direct Lesson Storage

Store lessons directly without transcript extraction:

```
/learn "Orphaned scheduled tasks silently fail with LastTaskResult=0x80070002 - technical (important)"
```

**Format**: `Lesson text - category (severity)`

- **category**: technical, process, tooling, decision, triage
- **severity**: critical (8), important (6), nice-to-know (4)
- Score ≥ 4 required to store

### stdin Mode

```bash
cat lessons.txt | /learn --stdin
# Each line: "Lesson text - category"
```

## Advanced Options

### Verbose Mode

Shows scoring breakdown for each candidate:

```
/learn --verbose

Candidate: "Terminal detection path mismatch"
  Novelty: 2/2 (new to CKS)
  Complexity: 2/2 (RCA required)
  Pattern: 2/2 (repeatable)
  Impact: 1/2 (saves time)
  Total: 7/8 ✓ STORE
```

### Dry Run

Shows what would be stored without actually storing:

```
/learn --dry-run

Would store 2 lessons (dry run, not stored):
1. [score: 7] Terminal detection path mismatch
2. [score: 6] Session isolation via ConsoleHost
```

## Technical Details

### Pipeline

```
transcript → candidates → novel → scored → keepers
             [patterns]   [CKS]   [score]  [≥4]
```

### Scoring Formula

```python
total = (
    novelty_score +      # 0-2 from CKS check
    complexity_score +   # 0-2 from RCA flags
    pattern_score +      # 0-2 from repeatable flags
    impact_score        # 0-2 from architectural flags
)
```

### Threshold Rationale

| Score | Meaning | Action |
|-------|---------|--------|
| 6-8 | High value | Always store |
| 4-5 | Medium value | Store if novel |
| 0-3 | Low value | Skip |

## Related Commands

- `/cks` - Direct knowledge storage
- `/search` - Search CKS/CHS for patterns
- `/cooldown` - Deprecated (use `/learn` instead)

## Quick Start

```bash
# End of session
/learn

# After fixing a bug
/learn

# Check what would be stored
/learn --dry-run
```
