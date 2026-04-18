# Output Format Reference

## Full Output Template

```yaml
## DUF-NSE Analysis: [change description]

**Risk Score:** [0.0-1.0] ([CRITICAL/HIGH/MEDIUM/LOW])
**Checks Run:** [list of checks actually performed]

### Push State
[Pushed / Not yet pushed -- inferred from conversation]

### Findings
- Pre-mortem: [one sentence failure scenario]
- Inversion: [one sentence obvious risk]
- Second-Order: [one sentence consequence] - SKIP for Trivial changes
- Red Team: [one sentence attack vector] - SKIP for Trivial/Moderate
- Empty Test: [one sentence edge case to check] - SKIP for Trivial
- Blast Radius: [one sentence dependency impact]
- Observability: [one sentence logging concern] - SKIP for Trivial
- Assumptions: [one sentence unverified belief] - SKIP for Trivial
- Rollback: [one sentence revert strategy]
- Value Reveal: [one sentence upside] - SKIP for Trivial

### Action Items

**Priority (Critical/Fixes)**
**1** - [Highest Priority Fix] - [WHY it matters]
**2** - [Critical Verification] - [WHY it matters]

**Maintenance (Cleanup/Tech Debt)**
**3** - [Cleanup Task] - [WHY]
**4** - [Tech Debt Item] - [WHY]

**Suggestions (Optional)**
**5** - /design - [Why architectural review is needed]
**6** - /test - [Why specific testing is needed]
**7** - [optimization/refactor] - [WHY]

**Git Operations**
**d** - push (include ONLY if no push command was seen in this conversation)

**x** - all (execute all Priority and Maintenance items)
**0** - none (skip action items)

### Assessment
[Overall: Safe to proceed / Needs review / High risk]
[Risk Score: 0.0-1.0] ([CRITICAL/HIGH/MEDIUM/LOW])
[Tier/Size/Kind breakdown if applicable]
```

## Action Items Rules

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

**Additional rules:**
- **Group items** by importance (Priority/Maintenance/Suggestions).
- **Omit N/A items**: If a category (e.g. /design) is not needed, do NOT list it.
- **Single-character selection**: Maintain 1-9, a-z selection IDs.
- **x** = Execute all Priority + Maintenance items.
- **0** = Skip all.
