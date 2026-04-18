# Technical Pattern Detection for extract_signals.py

## Overview

Add technical pattern detection to capture implementation learnings that are currently missed by conversational-only patterns. The GitHub search routing fix session produced 4 high-value lessons (scores 5-7) that were not captured because they described technical insights, not user corrections.

## Architecture

**Current Structure** (3 pattern categories):
```python
CORRECTION_PATTERNS = [...]  # "no, don't do X, do Y"
APPROVAL_PATTERNS = [...]   # "yes, perfect, great"
QUESTION_PATTERNS = [...]   # "have you considered X"
```

**Enhanced Structure** (7 pattern categories):
```python
CORRECTION_PATTERNS = [...]      # Existing (conversational)
APPROVAL_PATTERNS = [...]       # Existing (conversational)
QUESTION_PATTERNS = [...]       # Existing (conversational)

IMPLEMENTATION_PATTERNS = [...]  # NEW: "simple override fixed", "9 lines eliminated bugs"
ARCHITECTURE_PATTERNS = [...]    # NEW: "repo indicator override", "phrase-level context"
TEST_PATTERNS = [...]            # NEW: "all tests passing", "test caught regression"
DOCUMENTATION_PATTERNS = [...]   # NEW: "pattern validation prevented bugs"
```

**Detection Pipeline** (unchanged):
```
Phase 1: Regex detection (all 7 pattern categories)
Phase 2: Semantic analysis (optional AI enhancement)
Phase 3: Novelty detection (CKS daemon)
Phase 4: Implicit patterns (retry, tool discovery)
Phase 5: Workflow assumptions (external verification)
```

**Integration Point**:
- Add new patterns after line 92 in `extract_signals.py`
- Add detection loop in main extraction (lines 194-262)
- Signal structure unchanged: confidence, type, content, context, skills, description

## Data Flow

```
Transcript → extract_signals()
                ↓
        User Messages (role='user')
                ↓
    ┌───────────┴───────────┐
    │                       │
Regex Detection         Semantic Analysis
    │                       │
    └───────────┬───────────┘
                ↓
        Signal List
                ↓
    Novelty Check (CKS)
                ↓
        Novel Signals
                ↓
    group_by_skill()
                ↓
    suggestions.json
```

**No changes to data flow** - only adding new pattern categories to existing detection.

## Error Handling

**Regex Pattern Safety**:
- All patterns use `(?i)` flag for case-insensitive matching
- Non-capturing groups `(?:...)` to avoid extraction errors
- Optional quantifiers `?` to handle missing groups
- `match.groups()` validation before extraction

**Missing Groups Handling**:
```python
if match.groups():
    # Extract from groups
else:
    # Use full content as fallback
```

**Import Errors**:
- Pattern imports handled via try/except (same as existing imports)
- Missing modules emit warnings but don't crash extraction

## Test Strategy

**Unit Tests** (test_extract_signals.py):

1. **IMPLEMENTATION_PATTERNS** - Positive cases:
   - "simple keyword override fixed false positives"
   - "9 lines of code eliminated bugs"
   - "pattern validation documentation prevented issues"
   - "Test-driven development prevented regression"

2. **IMPLEMENTATION_PATTERNS** - Negative cases:
   - "simple code change" (too vague, no outcome)
   - "wrote some code" (no learning)
   - "fixed bug" (too generic, no mechanism)

3. **ARCHITECTURE_PATTERNS** - Positive cases:
   - "repo indicator overrides code keywords"
   - "phrase-level context detection worked"
   - "pattern validation template prevented false positives"

4. **ARCHITECTURE_PATTERNS** - Negative cases:
   - "code architecture" (too generic)
   - "repository search" (no mechanism)
   - "design pattern" (no outcome)

5. **TEST_PATTERNS** - Positive cases:
   - "all tests passing, test caught regression"
   - "pytest revealed edge case"
   - "test suite validated fix"

6. **TEST_PATTERNS** - Negative cases:
   - "tests" (too generic)
   - "pytest" (tool name, no learning)
   - "passing" (no context)

7. **DOCUMENTATION_PATTERNS** - Positive cases:
   - "pattern validation documentation prevented bugs"
   - "SKILL.md updated with lessons"
   - "documentation template caught issue"

8. **DOCUMENTATION_PATTERNS** - Negative cases:
   - "updated docs" (too vague)
   - "readme" (no learning)
   - "markdown" (format, not insight)

9. **Backward Compatibility**:
   - All existing CORRECTION/APPROVAL/QUESTION patterns still work
   - Signal structure unchanged
   - Hook execution time <5 seconds

10. **Integration Test**:
    - Run extract_signals.py on GitHub search routing transcript
    - Verify 4 technical lessons captured
    - Verify suggestions.json created successfully

## Standards Compliance

**Python Standards** (`/code-python`):
- Use `r"..."` raw strings for regex patterns (avoid escape issues)
- Type hints: `list[dict[str, Any]]` for signal lists
- Docstrings: Google style for all functions
- ruff linting: Must pass
- pytest: Async tests where applicable

**Testing Standards** (`/code-standards`):
- TDD: RED → GREEN → REFACTOR for all changes
- No mocking: Use real pattern matching, not mock objects
- Coverage: 90%+ for new code paths
- Integration tests: Real transcript, not synthetic data

## Ramifications

**Impact on existing code**:
- ✅ Zero breaking changes (additive only)
- ✅ Signal structure unchanged (backward compatible)
- ✅ Existing patterns work identically
- ✅ Hook execution time impact <1 second (4 new regex checks)

**Migration requirements**:
- None (additive feature)

**Performance impact**:
- Regex detection: +4 pattern lists (negligible, ~10ms)
- Semantic analysis: unchanged (optional)
- Novelty detection: unchanged (CKS daemon)
- Hook execution: <5 seconds total (tested)

**Documentation updates**:
- Update `reflect/SKILL.md` with technical pattern examples
- Add pattern validation documentation to `reflect/`
- Update hook integration docs if needed

## Pre-Mortem Analysis

**Failure Scenario**: "It's 6 months later. Technical pattern detection was abandoned because it produced too many false positives and filled CKS with noise."

### Top 6 Risk Priorities:

1. **[RISK:9] False positives flood CKS with low-value signals**
   - Prevent: High confidence threshold (0.75+) for technical patterns
   - Warning: CKS storage rate increases 5x+
   - Owner: Implementation validation

2. **[RISK:6] Patterns too specific miss actual learnings**
   - Prevent: Balance specificity (mechanism + outcome required)
   - Warning: Technical lessons still not captured
   - Owner: Pattern refinement

3. **[RISK:6] Hook timeout during transcript processing**
   - Prevent: Optimize regex, limit pattern complexity
   - Warning: Hook execution >5 seconds
   - Owner: Performance monitoring

4. **[RISK:6] Breaking existing pattern detection**
   - Prevent: Additive changes only, no modifications to existing patterns
   - Warning: Conversational signals stop working
   - Owner: Backward compatibility testing

5. **[RISK:3] Regex patterns brittle for multi-language**
   - Prevent: English-only for technical patterns (document limitation)
   - Warning: Non-English technical learnings missed
   - Owner: Documentation update

6. **[RISK:3] Signal structure becomes inconsistent**
   - Prevent: Follow existing signal schema exactly
   - Warning: Downstream processing breaks
   - Owner: Schema validation
