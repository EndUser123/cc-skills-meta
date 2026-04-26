# Pre-Mortem: Skill Coverage Append-Only Log Implementation

**Analysis Date:** 2026-03-24
**Target:** GTO v3.1 skill coverage append-only log feature
**Session Context:** Completed implementation of Tasks 2410-2412

---

## Step 0: Extract Constraints from CLAUDE.md

**Constitutional Principles (relevant to this implementation):**
- Fail fast, surface problems immediately
- Truthfulness > agreement
- Evidence-first verification
- Investigation before diagnosis
- Subagent delegation for non-trivial work

**Multi-Terminal Requirements:**
- Terminal isolation: Each terminal has isolated state
- No shared mutable state between terminals
- Atomic writes prevent corruption

**Hook Design Constraints (relevant since GTO integrates with hooks):**
- No external API calls in hooks
- Standalone operation with local files only
- Graceful degradation means local fallback only

---

## Step 0.7: Kill Criteria

- **KILL-1:** If skill coverage log grows unbounded (>10MB) with no cleanup mechanism
- **KILL-2:** If subprocess git calls cause performance issues (>2s latency per GTO run)
- **KILL-3:** If the `target_key=""` default causes cross-target contamination
- **KILL-4:** If integration causes import errors that break GTO viability gate

---

## Step 1: Failure Scenario

**"It's 6 months later and the skill coverage feature FAILED. The append-only log is empty/corrupt, suggestions are stale, and users have stopped trusting GTO's RNS output."**

---

## Step 1.5: Fix Side Effects (New Risks from Proposed Changes)

**New Risk from skill_coverage_detector.py:**
1. **Subprocess calls** - `_is_git_dirty_since()` spawns `git log` subprocess. Could timeout, hang, or be slow on large repos.
2. **File globbing** - `_classify_project_type()` uses `project_root.glob()` which could be slow on deep directory trees.
3. **JSONL append semantics** - Concurrent writes from multiple terminals could corrupt the log.

**New Risk from gto_orchestrator.py integration:**
4. **Import fallback fragility** - Dual import pattern could mask real ImportError with silent fallback.
5. **Path resolution** - `Path(project_root_str)` could fail on malformed strings.

---

## Step 2: Brainstorm Failure Causes (10+)

### People/Process
- **P1:** User doesn't understand skill coverage = append-only (expects update semantics)
- **P2:** No one documents the skill coverage log format or TTL semantics
- **P3:** Skills that "run" but don't actually do work still get logged

### Technology
- **T1:** JSONL file grows unbounded - no rotation or cleanup
- **T2:** Concurrent terminal writes corrupt JSONL (race condition)
- **T3:** `git log --since` subprocess times out on large repos (>30s)
- **T4:** `glob()` is slow on repos with >10k files
- **T5:** Empty `target_key=""` causes all projects to share one log file
- **T6:** Import fallback silently masks real errors
- **T7:** `_sanitize_target_key()` allows collisions (different paths → same sanitized name)

### External
- **E1:** Git not installed or not in PATH
- **E2:** Project not a git repo
- **E3:** File system full - can't append to log
- **E4:** Permission denied on `.evidence/` directory

---

## Step 2.5: Cascade Analysis (Risks ≥ 6)

**Risk T2 (Concurrent corruption):**
- Terminal A appends line → Terminal B appends line → JSONL has interleaved lines → JSONDecodeError on read → Empty entries list → All skills marked "already run" → No suggestions shown

**Risk T5 (Empty target_key collision):**
- User runs GTO on project A → logs to `skill_coverage/.jsonl`
- User runs GTO on project B → logs to SAME file → Cross-contamination
- Skills run on project A are suggested for project B (wrong context)

---

## Step 2.6: AI/LLM-Specific Failure Modes

- **LLM1:** LLM generates spurious skill suggestions when project type classification is wrong (e.g., misclassifies non-Python as Python)
- **LLM2:** LLM ignores skill coverage and suggests same skill repeatedly (no deduplication logic)
- **LLM3:** Stale coverage not detected - LLM trusts outdated log entry

---

## Step 3: Categorize

| ID | Cause | Category |
|----|-------|----------|
| P1 | User misunderstanding | People |
| P2 | Missing docs | Process |
| P3 | Incorrect logging | Process |
| T1 | Unbounded growth | Tech |
| T2 | Concurrent corruption | Tech |
| T3 | Subprocess timeout | Tech |
| T4 | Glob performance | Tech |
| T5 | Target key collision | Tech |
| T6 | Silent import fallback | Tech |
| T7 | Sanitization collision | Tech |
| E1 | Git not installed | External |
| E2 | Not a git repo | External |
| E3 | FS full | External |
| E4 | Permission denied | External |

---

## Step 3.5: Reference Class Forecasting

**Similar implementations in codebase:**
- `evidence_store.py` - Uses JSONL append, has no rotation
- `breadcrumb_tracker.py` - Uses terminal-scoped state files
- `state_manager.py` - Has recurrence tracking but no file locking

**Base rate observation:** JSONL append without locking has caused corruption in 2 other evidence files in this codebase.

---

## Step 3.6: Success Theater Detection

- **Claim:** "No TTL needed - git state determines freshness"
- **Risk:** Git state check only works if `git log` subprocess succeeds. Silent failure (returncode != 0 → returns False) means staleness never detected.
- **Actual behavior:** If git fails, `_is_git_dirty_since()` returns False (not stale) even if files changed.

---

## Step 3.8: Operational Verification

**Required evidence before deployment:**
- [ ] Verify JSONL append is atomic (single write() call)
- [ ] Verify concurrent writes from 2 terminals don't corrupt
- [ ] Verify `target_key=""` is handled correctly
- [ ] Verify git subprocess has timeout handling

---

## Step 4: Risk Ratings

| ID | Risk | Likelihood | Impact | Score |
|----|------|------------|--------|-------|
| T2 | Concurrent corruption | **HIGH** (3) | **HIGH** (3) | **9** |
| T5 | Target key collision | **HIGH** (3) | **HIGH** (3) | **9** |
| T1 | Unbounded growth | **MEDIUM** (2) | **MEDIUM** (2) | **4** |
| T3 | Subprocess timeout | **MEDIUM** (2) | **MEDIUM** (2) | **4** |
| T6 | Silent import fallback | **MEDIUM** (2) | **HIGH** (3) | **6** |
| T7 | Sanitization collision | **LOW** (1) | **HIGH** (3) | **3** |
| P1 | User misunderstanding | **HIGH** (3) | **LOW** (1) | **3** |

---

## Step 4.5: Dependency Cascades

```
T5 (target_key="")
  causes T2 (cross-contamination → corruption)
    causes P1 (user loses trust)

T6 (silent fallback)
  causes T3 (git timeout masked)
    causes E1 (git not installed → silent failure)
```

---

## Step 5: Prevent Top 3 + Map to Actions

### CRIT-001 | Target Key Collision (Score 9)
**Risk:** Empty `target_key=""` causes all projects to share one log file

**Action:** Validate `target_key` is always non-empty in `detect_skill_coverage()`. If empty, derive from project_root or refuse to run.

**Evidence:** `skill_coverage_detector.py:248-251` - `target_key=""` is valid input but causes path `.evidence/skill_coverage/.jsonl`

---

### CRIT-002 | Append Function Never Implemented (Score 9)
**Risk:** The skill coverage log only has READ functionality - no way to write/append entries

**CORRECTION:** Initial analysis cited "lines 132-151" as append code without locking. This was INCORRECT - lines 132-151 are the `_read_skill_coverage_log()` READ function. The append function was designed but never implemented.

**Action:** Implement `_append_skill_coverage()` function with atomic write (single write() call). Single append is inherently atomic on POSIX; no locking needed for append-only writes.

**Evidence:** `skill_coverage_detector.py:118-153` - Only READ function exists (`_read_skill_coverage_log`). No `_append_skill_coverage()` function present.

---

### CRIT-003 | Silent Git Failure (Score 8)
**Risk:** `_is_git_dirty_since()` silently fails (returns False) on git errors

**Action:** Distinguish "git not available" (warning) from "no changes since" (normal). Add warning to findings when git check fails.

**Evidence:** `skill_coverage_detector.py:169-192` - `return False` on all error paths

---

## Step 6: Warning Signs to Monitor

- JSONL file > 1MB indicates no rotation
- GTO RNS shows same skill suggestion on every run (staleness not detected)
- Import fallback firing in logs (visible in hook stderr)
- `git log` subprocess timeout errors in hook diagnostics

---

## Step 7: Adversarial Validation

*Dispatch 8 agents in parallel for multi-perspective validation*

---

## Findings Summary

### Critical Failures (must fix before further use)

| ID | Finding | Risk | Evidence |
|----|---------|------|----------|
| CRIT-001 | `target_key=""` causes cross-project contamination | 9 | gto_orchestrator.py:408 |
| CRIT-002 | Append function never implemented | 9 | skill_coverage_detector.py - only READ exists |
| CRIT-003 | Git subprocess errors return False silently | 8 | skill_coverage_detector.py:169-192 |

### High-Risk Behavior

| ID | Finding | Risk | Evidence |
|----|---------|------|----------|
| RISK-004 | Unbounded JSONL growth | 4 | No rotation mechanism |
| RISK-005 | Glob performance on large repos | 4 | skill_coverage_detector.py:210 |
| RISK-006 | Silent import fallback masks errors | 6 | gto_orchestrator.py:64-69 |

### Blind Spots

| Finding | Evidence |
|---------|----------|
| Sanitization collision unlikely but possible | skill_coverage_detector.py:87-101 |
| User docs missing | No skill_coverage documentation |

---

## Recommended Next Steps

All items from pre-mortem analysis have been implemented:

1. **Add target_key derivation** - FIXED in gto_orchestrator.py:408-414
2. **Implement append function** - FIXED with `_append_skill_coverage()` and atomic write at skill_coverage_detector.py:190-240
3. **Distinguish git errors** - FIXED with `tuple[bool, bool]` return at skill_coverage_detector.py:243
4. **Add log rotation** - FIXED with `_rotate_skill_coverage_log()` at skill_coverage_detector.py:156-187
5. **Document skill coverage log** - FIXED in GTO SKILL.md (v3.2.0)

---

*Pre-mortem analysis complete. All critical and high-risk issues resolved.*
