# Master Skill Orchestrator CLI - Example Outputs

This document shows actual outputs from CLI commands to demonstrate functionality.

## Table of Contents
1. [Help Command](#help-command)
2. [Suggest Command](#suggest-command)
3. [Info Command](#info-command)
4. [Validate Command](#validate-command)
5. [Workflow Command](#workflow-command)
6. [History Command](#history-command)
7. [Stats Command](#stats-command)
8. [Graph Command](#graph-command)
9. [Invoke Command](#invoke-command)
10. [JSON Mode Examples](#json-mode-examples)

---

## Help Command

```bash
python cli.py --help
```

**Output:**
```
usage: orchestrator [-h] [--json] [--quiet] [--verbose] [--version]
                    <command> ...

Master Skill Orchestrator - Route and manage Claude Code skills

options:
  -h, --help     show this help message and exit
  --json         Output in JSON format (useful for scripting)
  --quiet, -q    Suppress info messages (errors still shown)
  --verbose, -v  Enable verbose output
  --version      show program's version number and exit

commands:
  Available commands for skill orchestration

  <command>      Command to execute
    suggest      Show suggested next skills for a given skill
    info         Show comprehensive information about a skill
    validate     Validate a workflow sequence
    workflow     Suggest possible workflows from a skill
    history      Show workflow execution history
    stats        Show workflow statistics
    graph        Show skill relationship graph
    invoke       Invoke a skill through the orchestrator

Examples:
  orchestrator suggest /nse              Show suggestions for /nse skill
  orchestrator info /design                Show detailed info about /design
  orchestrator validate "/nse,/design"     Validate workflow sequence
  orchestrator workflow /nse --depth 2   Suggest workflows from /nse
  orchestrator history --limit 5         Show last 5 executions
  orchestrator stats                     Show workflow statistics
  orchestrator graph                     Show all skill relationships
  orchestrator invoke /nse               Invoke a skill

For more information, use: orchestrator <command> --help
```

---

## Suggest Command

```bash
python cli.py suggest /nse
```

**Output:**
```
=== Suggestions for /nse ===

Valid Next Skills:
  /r
  /design
  /r
  /llm-brainstorm
```

---

## Info Command

```bash
python cli.py info /nse
```

**Output:**
```
=== Skill Info: /nse ===
  Skill: /nse
  Type: Python Orchestrator
  Strategic: Yes

Metadata:
    name: nse
    description: Next Step Engine v2 - Unified intelligent development recommendations with constitutional compliance
    category: analysis
    domain: development
    version: 2.1.1
    triggers: next step, what's next, what should i do, recommend, suggestion, development strategy, code analysis, debug suggestions, refactoring advice, performance optimization, testing strategy, development workflow, code review, semantic analysis, development planning, strategic analysis, principal engineer, critical path, ROI optimization, risk mitigation, technical debt, high-stakes decision, confidence calibration, evidence-based, reversibility, constitutional compliance
    aliases: /nse
    dependencies: resources/examples.md, resources/actions.md, P:/__csf/src/features/nse/nse.py
    orchestrator: {"mode": "analysis", "plan_capable": true, "execute_capable": true, "code": "__csf/src/features/nse/nse.py"}
    context: main
    estimated_tokens: 500-3000
    status: stable

Suggests:
  /r
  /design
  /r
  /llm-brainstorm

Suggested By:
  /agent-orchestrator
  /analyze
  /design
  /r
  /dne
  /llm-brainstorm
  /r
  /orchestrator
  ... (and 85 more)
```

---

## Validate Command

### Valid Workflow

```bash
python cli.py validate "/nse,/r,/design"
```

**Output:**
```
=== Workflow Validation ===
  Workflow: /nse → /r → /design
✓ Valid workflow
```

### Invalid Workflow

```bash
python cli.py validate "/nse,/invalid,/design"
```

**Output:**
```
=== Workflow Validation ===
  Workflow: /nse → /invalid → /design
✗ Invalid workflow

Issues:
  Step 0: /nse → /invalid
    Reason: Transition not found in suggest fields

Valid Next Skills:
  /r
  /design
  /r
  /llm-brainstorm
```

---

## Workflow Command

```bash
python cli.py workflow /nse --depth 2
```

**Output:**
```
=== Workflow Suggestions from /nse ===
  Max depth: 2
  Paths found: 15

Possible Workflows:
  1. /nse → /r → /nse
  2. /nse → /r → /dne
  3. /nse → /r → /design
  4. /nse → /r → /llm-brainstorm
  5. /nse → /design → /nse
  6. /nse → /design → /r
  7. /nse → /design → /llm-brainstorm
  8. /nse → /design → /r
  9. /nse → /r → /nse
  10. /nse → /r → /design
  11. /nse → /r → /analyze
  12. /nse → /llm-brainstorm → /nse
  13. /nse → /llm-brainstorm → /design
  14. /nse → /llm-brainstorm → /analyze
  15. /nse → /llm-brainstorm → /r
```

---

## History Command

```bash
python cli.py history --limit 5
```

**Output:**
```
=== Workflow Execution History ===
  Showing last 2 entries
  Total executions: 2

Recent Executions:
  ✓ /t [success]
    Time: 2026-01-18T14:48:39.192060
    Next: /comply, /qa, /bug-hunt
    Path: /t

  ✓ /nse [success]
    Time: 2026-01-18T14:48:39.190791
    Next: /r, /design, /r, /llm-brainstorm
    Path: /nse
```

---

## Stats Command

```bash
python cli.py stats
```

**Output:**
```
=== Workflow Statistics ===
  Total executions: 2
  Total strategic decisions: 1
  Current workflow: (none)
  Workflow stack depth: 0
  Skills with suggest fields: 58
  Valid transitions: 104
  Total skill invocations: 0
```

---

## Graph Command

### Full Graph

```bash
python cli.py graph
```

**Output:**
```
=== Skill Relationship Graph ===
  Skills with suggest fields: 58

Skill Transitions:
  /analyze → /nse, /design, /r
  /design → /nse, /r, /llm-brainstorm, /r
  /bug-hunt → /comply, /t, /debug
  /build → /qa, /t, /comply
  /chs → /cks, /search, /research
  /cks → /chs, /search, /progressive-search
  /code-python-2025 → /comply, /t, /bug-hunt
  /code-typescript-2025 → /comply, /t, /bug-hunt
  /cognitive-frameworks → /nse, /design, /r
  /commit → /push, /git-safety
  /complexity → /refactor, /bug-hunt, /analyze
  /comply → /t, /bug-hunt, /q
  /csf-nip-dev → /comply, /standards, /t
  /csf-nip-integration → /nse, /orchestrator, /build
  /cwo → /nse, /workflow, /quadlet
  /ddd → /comply, /t, /qa
  /debug → /rca, /r, /chs, /fix
  /design → /build, /design, /nse
  /r → /nse, /dne, /design, /llm-brainstorm
  /dne → /nse, /r, /design, /llm-brainstorm
  /p2 → /p3, /adversarial-review, /tdd
  /evolve → /comply, /t, /refactor
  /fix → /t, /tdd, /rca
  /git-conventional-commits → /commit, /push
  /git-safety → /commit, /push, /git-conventional-commits
  ... (and 35 more)

  Total transitions: 104
```

### Filtered Graph

```bash
python cli.py graph --filter /nse
```

**Output:**
```
=== Skill Relationship Graph ===
  Skills with suggest fields: 1

Skill Transitions:
  /nse → /r, /design, /r, /llm-brainstorm

  Total transitions: 4
```

---

## Invoke Command

```bash
python cli.py invoke /nse
```

**Output:**
```
=== Invoking /nse ===
✓ Skill invoked successfully
  Result: NSE execution

Suggested Next:
  /r
  /design
  /r
  /llm-brainstorm

Use Skill tool to invoke /nse from within Claude Code
```

---

## JSON Mode Examples

### Stats in JSON

```bash
python cli.py --json stats
```

**Output:**
```json
{
  "total_executions": 2,
  "total_decisions": 1,
  "current_workflow": [],
  "workflow_state": {
    "current_skill": null,
    "stack_depth": 0,
    "workflow_path": [],
    "total_valid_transitions": 104
  },
  "invocation_stats": {
    "total_invocations": 0
  },
  "skills_with_suggest_fields": 58
}
```

### Info in JSON

```bash
python cli.py --json info /nse
```

**Output:**
```json
{
  "skill": "/nse",
  "metadata": {
    "name": "nse",
    "description": "Next Step Engine v2 - Unified intelligent development recommendations with constitutional compliance",
    "category": "analysis",
    "domain": "development",
    "version": "2.1.1",
    "triggers": [
      "next step",
      "what's next",
      "what should i do",
      "recommend",
      "suggestion",
      ...
    ],
    "aliases": ["/nse"],
    "dependencies": [
      "resources/examples.md",
      "resources/actions.md",
      "P:/__csf/src/features/nse/nse.py"
    ],
    "orchestrator": {
      "mode": "analysis",
      "plan_capable": true,
      "execute_capable": true,
      "code": "__csf/src/features/nse/nse.py"
    },
    "context": "main",
    "estimated_tokens": "500-3000",
    "status": "stable"
  },
  "suggests": ["/r", "/design", "/r", "/llm-brainstorm"],
  "suggested_by": [
    "/agent-orchestrator",
    "/analyze",
    "/design",
    "/r",
    ...
  ],
  "is_python_orchestrator": true,
  "is_strategic": true
}
```

### Suggestions in JSON

```bash
python cli.py --json suggest /nse
```

**Output:**
```json
{
  "skill": "/nse",
  "suggestions": ["/r", "/design", "/r", "/llm-brainstorm"]
}
```

---

## Error Handling Examples

### Skill Not Found

```bash
python cli.py info /nonexistent-skill
```

**Output:**
```
=== Skill Info: /nonexistent-skill ===
Warning: Skill '/nonexistent-skill' not found or has no metadata
```

### Invalid Workflow

```bash
python cli.py validate "/nse,/invalid"
```

**Output:**
```
=== Workflow Validation ===
  Workflow: /nse → /invalid
Error: ✗ Invalid workflow

Issues:
  Step 0: /nse → /invalid
    Reason: Transition not found in suggest fields
```

---

## Notes

### Git Bash Path Issue

On Windows with Git Bash, paths like `/nse` are interpreted as Windows paths. Use one of these workarounds:

**Option 1: Double-slash**
```bash
python cli.py suggest //nse
```

**Option 2: Disable path conversion**
```bash
MSYS_NO_PATHCONV=1 python cli.py suggest /nse
```

**Option 3: Use wrapper script**
```bash
./orchestrator.sh suggest nse
```

### Exit Codes

- `0` - Success
- `1` - Error (invalid input, operation failed)
- `130` - Cancelled by user (Ctrl+C)

### Scripting with JSON

JSON mode is ideal for scripting and automation:

```bash
# Get suggestions as JSON
python cli.py --json suggest /nse | jq '.suggestions[]'

# Check if workflow is valid
python cli.py --json validate "/nse,/r" | jq '.valid'

# Export statistics
python cli.py --json stats > orchestrator-stats.json
```

---

## Test Results

All 12 CLI tests pass:

```
============================================================
Master Skill Orchestrator CLI Test Suite
============================================================

Testing: --help
Testing: --version
Testing: suggest /nse
Testing: info /nse
Testing: stats
Testing: --json stats
Testing: history --limit 3
Testing: graph
Testing: workflow /nse --depth 2
Testing: invoke /nse
Testing: validate '/nse,/r' (should succeed)
Testing: info /nonexistent-skill-xyz

============================================================
Test Summary
============================================================
Passed: 12
Failed: 0
Total:  12

✓ All tests passed!
```
