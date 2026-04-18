# Pattern Refinement Workflow

**Purpose**: Monthly validation process to review technical patterns against real transcripts and add new patterns based on missed learnings.

**When**: Run monthly or after major sessions where important learnings may have been missed.

**Why**: Technical pattern detection requires ongoing refinement. Real-world usage reveals gaps that synthetic tests don't catch.

---

## Quick Start

```bash
# Run validation on a past transcript
python P:/.claude/skills/reflect/scripts/validate_pattern_coverage.py ~/.claude/history/session_YYYYMMDD.jsonl

# Example: Validate yesterday's session
python P:/.claude/skills/reflect/scripts/validate_pattern_coverage.py ~/.claude/history/session_20260310.jsonl
```

---

## Workflow Steps

### 1. Choose a Transcript

Select a past session that involved technical work:
- GitHub-style problem-solving (search routing, API design, debugging)
- Architecture decisions
- Implementation learnings
- Test discoveries

**Good candidates**: Sessions where you fixed bugs, implemented features, or made technical decisions.

### 2. Run Validation Script

```bash
python P:/.claude/skills/reflect/scripts/validate_pattern_coverage.py <transcript.jsonl>
```

**Output**:
- Pattern match summary (how many messages matched)
- Unmatched segments (potential missed learnings)
- Pattern type distribution (implementation, architecture, test, documentation)

### 3. Review Unmatched Segments

The script outputs unmatched segments that didn't match any pattern:

```
======================================================================
UNMATCHED SEGMENTS (Manual Review Required)
======================================================================

[Message 23]
The repo indicator override fixed the search routing issue
We should document this pattern for future sessions

[Message 45]
Test-driven development caught the race condition
Without tests, this would have been a production bug
```

**For each unmatched segment**:
1. Is this a genuine learning? (not just routine conversation)
2. What pattern would capture this?
3. Which category does it belong to? (implementation, architecture, test, documentation)

### 4. Add New Patterns (if needed)

If you identified genuine learnings:

**Edit**: `P:/.claude/skills/reflect/scripts/extract_signals.py`

Add patterns to the appropriate category:

```python
# Example: New implementation pattern
IMPLEMENTATION_PATTERNS = [
    # ... existing patterns ...
    r"(?i)repo\s+indicator\s+override\s+fixed",  # NEW
    r"(?i)TDD\s+caught\s+(?:race\s+condition|bug|regression)",  # NEW
]
```

**Pattern Design Guidelines**:
- Use `r"..."` raw strings (avoid escape issues)
- Use `(?i)` flag for case-insensitive matching
- Use non-capturing groups `(?:...)` for optional parts
- Test patterns against false positives (generic phrases)

### 5. Re-Run Tests

```bash
cd P:/.claude/skills/reflect
pytest tests/test_extract_signals_technical.py -v
```

**Verify**:
- New tests pass (positive cases)
- Existing tests still pass (no regressions)
- Negative case tests pass (no false positives)

### 6. Update Documentation (optional)

If patterns changed significantly, update:
- `plan.md` (pattern design section)
- Test files (add test cases for new patterns)
- This workflow doc (if process changed)

---

## Pattern Category Reference

### IMPLEMENTATION_PATTERNS
**Scope**: Code-level fixes with specific mechanisms
**Examples**:
- "simple override fixed false positives"
- "9 lines eliminated bugs"
- "keyword override resolved issue"

**What to include**:
- Specific mechanisms (override, elimination, keyword)
- Clear outcomes (fixed, resolved, eliminated)
- Technical changes (not just "code change")

**What to exclude**:
- Vague statements ("code change", "wrote code")
- No mechanism ("fixed bug")
- No outcome ("tried X")

### ARCHITECTURE_PATTERNS
**Scope**: Structural/system-level learnings
**Examples**:
- "repo indicator overrides code keywords"
- "phrase-level context detection worked"
- "pattern validation prevented false positives"

**What to include**:
- System-level patterns (repo, routing, context)
- Structural decisions (architecture, hierarchy)
- Integration learnings

**What to exclude**:
- Generic architecture terms ("code architecture")
- No mechanism ("design pattern")

### TEST_PATTERNS
**Scope**: Testing insights and validation
**Examples**:
- "all tests passing, test caught regression"
- "pytest revealed edge case"
- "test suite validated fix"

**What to include**:
- Test findings (caught, revealed, validated)
- Specific test tools (pytest, unittest)
- Test outcomes (passing, regression, edge case)

**What to exclude**:
- Generic mentions ("tests")
- Tool names only ("pytest")
- No context ("passing")

### DOCUMENTATION_PATTERNS
**Scope**: Documentation-driven learnings
**Examples**:
- "pattern validation documentation prevented bugs"
- "SKILL.md updated with lessons"
- "documentation template caught issue"

**What to include**:
- Documentation preventing issues
- Specific docs (SKILL.md, README.md, template)
- Documentation-driven fixes

**What to exclude**:
- Vague updates ("updated docs")
- Format mentions ("markdown")
- No learning ("read readme")

---

## Negative Pattern Filtering

The script automatically filters out segments matching negative patterns (exclusion patterns):

**Current negative patterns** (13 total):
- `simple code change` (too vague)
- `wrote some code` (no outcome)
- `fixed bug` (no mechanism)
- `code change` (no outcome)
- `made change` (too generic)
- ... (8 more)

**If a segment is incorrectly filtered**:
1. Review the negative pattern list
2. Check if the filter is too broad
3. Refine negative pattern to be more specific
4. Re-run validation

---

## Monthly Checklist

Run this checklist monthly to keep patterns fresh:

- [ ] Choose a recent technical session transcript
- [ ] Run `validate_pattern_coverage.py`
- [ ] Review unmatched segments for missed learnings
- [ ] Add new patterns if genuine learnings found
- [ ] Re-run tests: `pytest test_extract_signals_technical.py -v`
- [ ] Document pattern additions in commit message
- [ ] Track pattern evolution in `PATTERN_CHANGELOG.md` (optional)

---

## Example: Pattern Refinement Session

**Transcript**: GitHub search routing fix (2026-03-10)

**Unmatched segments found**: 4

**Review**:
1. "repo indicator override fixed search routing" → GENUINE LEARNING
   - Pattern: `r"(?i)repo\s+indicator\s+override\s+fixed"`
   - Category: ARCHITECTURE_PATTERNS
   - Action: Add to extract_signals.py

2. "wrote some code" → FILTERED (negative pattern)
   - Already caught by NEGATIVE_PATTERNS
   - Action: None

3. "phrase-level context detection worked" → GENUINE LEARNING
   - Pattern: `r"(?i)phrase.level\s+context\s+detection\s+worked"`
   - Category: ARCHITECTURE_PATTERNS
   - Action: Add to extract_signals.py

4. "simple code change" → FILTERED (negative pattern)
   - Already caught by NEGATIVE_PATTERNS
   - Action: None

**Result**: 2 new patterns added, 2 correctly filtered

---

## Troubleshooting

**Problem**: Too many unmatched segments to review

**Solution**:
- Focus on sessions with clear technical learnings
- Skip routine sessions (config changes, minor fixes)
- Use grep to filter unmatched output: `python validate_pattern_coverage.py transcript.jsonl | grep "UNMATCHED"`

**Problem**: Pattern matches too broadly (false positives)

**Solution**:
- Add more specific keywords to pattern
- Use negative patterns to filter generic phrases
- Test pattern against adversarial inputs

**Problem**: Script fails to load transcript

**Solution**:
- Check transcript path is correct
- Verify transcript is valid JSONL format
- Check file encoding is UTF-8

---

## Integration with Other Systems

**CKS**: High-value pattern refinements should be stored as CKS entries
**Tests**: Each new pattern should have test cases (positive + negative)
**Hooks**: Pattern changes don't require hook updates (self-contained)

---

**Last Updated**: 2026-03-10
**Next Review**: 2026-04-10 (monthly)
