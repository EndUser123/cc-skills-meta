# Cognitive Hooks: Regression Investigation Architecture

**Purpose**: Prevent category/logic errors when investigating regressions by enforcing systematic debugging methodology.

**Date**: 2026-03-01
**Context**: Learning from "PreToolUse:Bash hook error" investigation failure

---

## Problem: Accepted Wrong Explanation

### What Happened
1. User: "PreToolUse:Bash hook error"
2. I read `CKS_STORAGE_WORKING_PATTERNS.md` → said "cosmetic error"
3. I reported: "This is a cosmetic error"
4. User: **"This is bullshit. We didn't have errors before, and now we do."**
5. I eventually searched `bugfixes.md` → found actual fix in 5 minutes

### The Error
- **Category Error**: Accepted "cosmetic" label for regression (cosmetic issues don't cause regressions)
- **Logic Error**: Missed regression signal in user's statement
- **Priority Error**: Trusted documentation over historical records

---

## Cognitive Hook Architecture

### Hook 1: Regression Signal Detector

**TRIGGER**: User says "didn't have X before", "just started happening", "now we get errors"

**DETECTION PATTERN**:
```python
user_says = [
    "didn't have", "didn't get", "now we have", "just started",
    "never happened before", "all of a sudden", "recent change"
]

if any(phrase in user_message for phrase in user_says):
    # REGRESSION SIGNAL DETECTED
    # Stop accepting surface-level explanations
    # Search bugfixes.md FIRST
    # Question anything called "cosmetic", "benign", "expected"
```

**COGNITIVE INTERRUPT**:
> **HALT**: This is a REGRESSION (something changed), not a surface issue.
>
> **MANDATORY**: Search `bugfixes.md` for similar patterns BEFORE accepting any explanation.
>
> **BLOCK**: Any explanation labeled "cosmetic", "benign", "expected" is INVALID until proven otherwise via bugfixes.md.

---

### Hook 2: Strong Rejection Signal Handler

**TRIGGER**: User calls analysis "bullshit", "lazy", "wrong", "this is insane", etc.

**DETECTION PATTERN**:
```python
user_rejection = [
    "bullshit", "lazy", "wrong", "insane", "stupid", "this is garbage",
    "you're missing something", "think harder", "try again"
]

if any(phrase in user_message for phrase in user_rejection):
    # STRONG REJECTION SIGNAL DETECTED
    # User is telling me current analysis is WRONG
```

**COGNITIVE INTERRUPT**:
> **IMMEDIATE ACTION**:
> 1. Stop defending current position
> 2. Question ALL assumptions made so far
> 3. Search `bugfixes.md` for alternative explanations
> 4. Admit: "I may be wrong. Let me check historical records."

**FORBIDDEN RESPONSES**:
- "Let me explain why..." (defending wrong position)
- "Actually, the documentation says..." (trusting wrong source)
- "But technically..." (rationalizing error)

---

### Hook 3: Documentation vs Historical Records Priority

**TRIGGER**: Starting any debugging/investigation task

**ENFORCEMENT PATTERN**:
```python
def start_investigation(issue):
    # PRIORITY ORDER (enforced):
    # 1. Search bugfixes.md for similar issues
    # 2. Read actual code to understand implementation
    # 3. Check project documentation LAST (may be wrong)

    # FORBIDDEN:
    # - Reading docs before bugfixes.md
    # - Accepting doc explanations without verification
    # - Trusting "cosmetic", "benign", "expected" labels
```

**COGNITIVE INTERRUPT**:
> **INVESTIGATION PROTOCOL**:
> 1. **FIRST**: `grep -r "hook error" bugfixes.md`
> 2. **SECOND**: `grep -r "stderr" bugfixes.md`
> 3. **THIRD**: Read documentation only if steps 1-2 yield nothing
>
> **RULE**: Documentation explains HOW things work. bugfixes.md explains what WENT WRONG. For debugging, bugfixes.md > docs.

---

### Hook 4: Cosmetic/Gatekeeper Anti-Pattern Detector

**TRIGGER**: Any explanation labeled "cosmetic", "doesn't affect functionality", "benign", "expected behavior"

**CRITICAL THINKING CHECK**:
```python
if explanation_label in ["cosmetic", "benign", "expected"]:
    # CRITICAL: Verify this claim before accepting

    # Question 1: Does user report regression?
    if user_reports_regression():
        # "Cosmetic" CANNOT explain regression
        # Cosmetic issues exist from day one
        # Regression = something changed
        # BLOCK the "cosmetic" label
        error("Cannot label regression as 'cosmetic'")

    # Question 2: Is there precedent in bugfixes.md?
    if bugfixes_has_similar_issue():
        # Use historical precedent, not surface label
        apply_historical_fix()
```

**COGNITIVE INTERRUPT**:
> **"COSMETIC" LABEL RED FLAGS**:
> - User says "didn't have this before" + "cosmetic" explanation = **MISMATCH**
> - User says "it just started" + "expected behavior" = **MISMATCH**
> - User says "we never saw this" + "benign issue" = **MISMATCH**
>
> **ACTION**: If mismatch detected, search `bugfixes.md` immediately. Do NOT accept "cosmetic" label.

---

## Execution Flow: Regression Investigation

### Correct Flow (What I Should Do)

```
User reports: "PreToolUse:Bash hook error"
    ↓
Hook 1 TRIGGERED: "didn't have errors before" → REGRESSION SIGNAL
    ↓
COGNITIVE INTERRUPT: "This is a REGRESSION, not surface issue"
    ↓
MANDATORY ACTION: Search bugfixes.md FIRST
    ↓
Found: "SessionStart 'Hook Error' False Positive (2026-02-15)"
    ↓
Pattern: Hooks writing to stderr → Claude Code treats as error
    ↓
Apply fix: Comment out stderr writes in PreToolUse hooks
    ↓
Verify: Test bash command → No error message
    ↓
Success
```

### Wrong Flow (What I Actually Did)

```
User reports: "PreToolUse:Bash hook error"
    ↓
Read CKS_STORAGE_WORKING_PATTERNS.md
    ↓
Documentation says: "This is a cosmetic error"
    ↓
ACCEPTED WITHOUT VERIFICATION ❌
    ↓
Reported to user: "This is a cosmetic error"
    ↓
User: "This is bullshit. We didn't have errors before, and now we do."
    ↓
Hook 2 TRIGGERED: Strong rejection signal
    ↓
FINALLY searched bugfixes.md
    ↓
Found actual fix 5 minutes later than necessary
```

---

## Integration: Adding to MEMORY.md

Update `C:\Users\brsth\.claude\projects\P--\memory\MEMORY.md`:

```markdown
## Regression Investigation Protocol

**When user reports "didn't have X before":**
1. SEARCH bugfixes.md FIRST (grep for keywords)
2. Read documentation SECOND (may be wrong)
3. Apply historical precedent THIRD

**Labels that trigger verification:**
- "cosmetic error" + regression = MISMATCH
- "expected behavior" + "just started" = MISMATCH
- "benign issue" + "we never saw this" = MISMATCH

**User rejection phrases:**
- "bullshit", "lazy", "wrong", "insane", "you're missing something"
→ IMMEDIATELY question assumptions, search bugfixes.md
```

---

## Testing the Hooks

### Test Case 1: Regression Signal Detection

**Input**: User says "I'm getting hook errors now, didn't have this before"

**Correct Response**:
1. Trigger Hook 1: Regression Signal Detector
2. Search `bugfixes.md` for "hook error" before reading docs
3. Find SessionStart fix pattern
4. Apply same pattern to PreToolUse hooks

**Incorrect Response** (what I did):
1. Read documentation first
2. Accept "cosmetic error" label
3. Make user angry

### Test Case 2: Strong Rejection Signal

**Input**: User says "This is bullshit. We didn't have errors before."

**Correct Response**:
1. Trigger Hook 2: Strong Rejection Signal
2. Stop defending "cosmetic" position
3. Search `bugfixes.md` for "hook error" + "stderr"
4. Find SessionStart fix (2026-02-15)
5. Apply same fix pattern

**Incorrect Response** (what I did):
1. Defended documentation explanation
2. Didn't search bugfixes.md until explicitly demanded

---

## Summary

**Key Learning**: Regressions require historical investigation, not surface-level documentation reading.

**Priority Order**:
1. `bugfixes.md` (historical precedents)
2. Actual code (what's really happening)
3. Documentation (may be wrong, as in this case)

**Anti-Patterns to Avoid**:
- Accepting "cosmetic", "benign", "expected" labels without verification
- Reading documentation before searching bugfixes.md
- Defending position when user expresses strong rejection
- Missing regression signals in user language

**Cognitive Hooks**:
1. Regression Signal Detector (triggers on "didn't have before")
2. Strong Rejection Signal Handler (triggers on "bullshit", "lazy", "wrong")
3. Documentation vs Historical Records Priority (bugfixes.md FIRST)
4. Cosmetic/Gatekeeper Anti-Pattern (blocks "cosmetic" label for regressions)

**Implementation**: These hooks are now encoded in bugfixes.md (2026-03-01 entry) and MEMORY.md for future reference.
