---
name: truth
description: Truth Constitution Command - Verify claims using actual evidence
category: validation
domain: validation
version: 1.1.0
triggers: []
context: main
estimated_tokens: 200-1000
status: stable
aliases:
  - '/truth'
suggest:
  - /comply
---


# /truth - Truth Constitution Command

## Purpose

Verifies claims using actual evidence. Reads files, runs commands, and shows output to prove or disprove assertions.

## Project Context

### Constitution / Constraints

- PART T (Truthfulness): Report test failures honestly, never hide issues
- Evidence-first: Verify claims with actual code/data before conclusions
- Read files before making claims about them
- Run exact commands to verify behavior

### Technical Context

- Uses Read, Bash tools for verification
- Works with any file type or command output
- No speculation - only actual evidence

### Architecture Alignment

- Verification pattern: Independent check of claims
- Anti-speculation: Never claim "probably" or "likely"

## Your Workflow

1. Identify claim(s) to verify
2. Read actual file/code being referenced
3. Run commands to verify behavior
4. Show actual output (don't say "verified")
5. Correct any false claims with evidence

## Validation Rules

### Prohibited Actions

- Do NOT say "verified" without showing evidence
- Do NOT speculate or use "probably", "likely"
- Do NOT accept claims at face value

### Best Practices

#### Regex Pattern String Escaping

When writing Python regex patterns with character classes containing quote characters (`['"`]`), match the outer string delimiter to avoid conflicts:

- **Pattern has double quotes inside:** Use `r'...'` (single-quoted raw string)
  ```python
  # CORRECT: Character class has ", so use ' as outer delimiter
  re.compile(r'pattern["\`](.+?)["\`]')
  ```

- **Pattern has single quotes inside:** Use `r"..."` (double-quoted raw string)
  ```python
  # CORRECT: Character class has ', so use " as outer delimiter
  re.compile(r"pattern['`](.+?)['`]")
  ```

**Verification:** Always compile regex patterns immediately after creation with `re.compile()` to catch syntax errors early.

### Required Format

For each claim:
- CLAIM: [the claim made]
- STATUS: VERIFIED | FALSE | PARTIAL | UNVERIFIED
- EVIDENCE: [actual file content, command output, or test results]

## Adversarial Verification Mode (v2.0 NEW)

> [!IMPORTANT]
> **Challenge claims systematically, not deferentially.**

**When invoked with `--adversarial` flag:**

1. **Extract all claims** from previous message
2. **Challenge each claim** - Demand evidence
3. **Mark verdicts** - VERIFIED | FALSE | PARTIAL | UNVERIFIED
4. **Output format**:
   ```
   CLAIM: "[claim text]"
   STATUS: VERIFIED | FALSE | PARTIAL | UNVERIFIED
   EVIDENCE: [actual evidence or "none provided"]
   CORRECTION: [if FALSE, show correct information]
   ```

**Example:**
```
CLAIM: "hook returns {}"
STATUS: FALSE
EVIDENCE: Hook output from .claude/state/hook_output.json shows:
  {"hookSpecificOutput": {"result": "success"}}
CORRECTION: Hook does NOT return {}. Actual output contains hookSpecificOutput field.
```

**Usage:**
```bash
/truth --adversarial
```


## ⚡ EXECUTION DIRECTIVE

**IMMEDIATELY verify claims using actual evidence.**

### DEFAULT (no arguments)

Verify all claims from the immediately preceding assistant message.

### WITH ARGUMENTS

Treat arguments as claims to verify, or as specific questions to investigate.

## Verification Method

For each claim:

1. **Read** the actual file/code being referenced
2. **Run** commands to verify behavior
3. **Show** actual output (don't say "verified")
4. **Correct** any false claims with evidence

## Output Format

```
CLAIM: [the claim made]
STATUS: VERIFIED | FALSE | PARTIAL | UNVERIFIED
EVIDENCE: [actual file content, command output, or test results]
```

If claim is FALSE, show correction with evidence.

## When to Use

- After an assistant makes claims you want verified
- To check if code exists before referencing it
- To validate assumptions about file contents
- To audit command outputs
- To prove or disprove assertions

## Examples

```bash
# Verify previous claims
/truth

# Verify specific claim
/truth does this file exist

# Audit a statement
/truth validate that the test passes
```
