---
name: evidence-applicability
version: "1.0.0"
status: "stable"
description: Evidence must apply to the claim's context, not just support its content.
category: verification
triggers:
  - 'git show'
  - 'the file says'
  - 'the code does'
  - 'the spec requires'
  - 'documentation states'
aliases:
  - '/evidence-context'
suggest:
  - /research
---

## Purpose

Evidence must apply to the claim's context, not just support its content.

Real evidence + correct content + wrong context = invalid claim.

## Before Citing Evidence, Verify Alignment

| Dimension | Question | Mismatch Signals |
|-----------|----------|------------------|
| Temporal | Is this current enough for a present-tense claim? | `git show <old-commit>:`, old logs, cached results |
| Scope | Is this from the same system/branch/project? | Cross-project grep, different repo, other branch |
| Authority | Is this canonical, not draft/deprecated? | "proposed", "draft", "v1" when v2 exists, archived/ |
| Identity | Is this the actual entity, not similar-named? | Same function name in different module |

## Rule

Present-tense claims require present-state evidence. Historical evidence supports "was" claims, not "is" claims.

## Anti-Patterns

| Pattern | Problem |
|---------|---------|
| `git show abc123:file` → "The file says..." | Historical commit ≠ current state |
| `grep -r "pattern" P:/` finds match → "Project X has..." | May be different project than discussed |
| Read `docs/draft-spec.md` → "The spec requires..." | Draft ≠ authoritative |
| Found `utils.py:parse()` → "The parse function does..." | May be different parse() than intended |

## Required Verification

1. Find evidence (git show, grep, read)
2. CHECK: Does this evidence apply to my claim's context?
   - If historical: verify current state before present-tense claim
   - If cross-project: verify same project as discussion
   - If documentation: verify canonical, not draft/deprecated
3. If mismatch: qualify the claim ("In commit X...", "Draft spec says...", "A different module's parse()...")

## Trigger Phrases Requiring Applicability Check

- "The constitution says..." — verify current CLAUDE.md, not historical
- "The code does..." — verify current file state
- "Tests show..." — verify test ran against current code
- "Documentation states..." — verify canonical source, not draft

## Trigger

Activate when:
- Using `git show` to make present-tense claims
- Citing grep results from broad searches
- Quoting documentation as authority
- Making claims about "the code" or "the file"
