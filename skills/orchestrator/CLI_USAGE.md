# Master Skill Orchestrator CLI

## Overview

A robust command-line interface for the Master Skill Orchestrator with colored output, JSON export, and comprehensive error handling.

## Installation

The CLI is located at `P:/.claude/skills/orchestrator/cli.py`.

## Quick Start

### Windows CMD/PowerShell

```powershell
cd P:\.claude\skills\orchestrator
python cli.py suggest /nse
python cli.py info /design
python cli.py stats
```

### Git Bash (Windows)

Git Bash interprets `/nse` as a Windows path. Use one of these workarounds:

**Option 1: Double-slash (simplest)**
```bash
cd P:/.claude/skills/orchestrator
python cli.py suggest //nse
python cli.py info //design
```

**Option 2: Use the wrapper script**
```bash
cd P:/.claude/skills/orchestrator
./orchestrator.sh suggest nse      # No leading / needed
./orchestrator.sh info arch
./orchestrator.sh stats
```

**Option 3: MSYS_NO_PATHCONV=1**
```bash
cd P:/.claude/skills/orchestrator
MSYS_NO_PATHCONV=1 python cli.py suggest /nse
```

## Commands

### suggest - Show suggested next skills

Show which skills are recommended after a given skill.

```bash
python cli.py suggest <skill>
```

**Example:**
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

### info - Show comprehensive skill information

Display detailed metadata, suggestions, and relationships.

```bash
python cli.py info <skill>
```

**Example:**
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
    description: Next Step Engine v2
    category: analysis
    ...

Suggests:
  /r
  /design
  /r
  /llm-brainstorm

Suggested By:
  /analyze
  /design
  /r
  ...
```

### validate - Validate workflow sequence

Check if a sequence of skills is valid.

```bash
python cli.py validate <skill1,skill2,...>
```

**Example:**
```bash
python cli.py validate "/nse,/r,/design"
```

**Output:**
```
=== Workflow Validation ===
  Workflow: /nse → /r → /design
✓ Valid workflow
```

### workflow - Suggest possible workflows

Generate all possible workflow paths from a starting skill.

```bash
python cli.py workflow <skill> [--depth N]
```

**Example:**
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
  ...
```

### history - Show execution history

Display recent skill invocations.

```bash
python cli.py history [--limit N]
```

**Example:**
```bash
python cli.py history --limit 5
```

**Output:**
```
=== Workflow Execution History ===
  Showing last 5 entries
  Total executions: 25

Recent Executions:
  ✓ /nse [success]
    Time: 2026-01-18T14:48:39
    Next: /r, /design, /r
    Path: /nse

  ✓ /r [success]
    Time: 2026-01-18T14:48:40
    Next: /nse, /dne
    Path: /nse → /r
```

### stats - Show workflow statistics

Display overall statistics about skill usage.

```bash
python cli.py stats
```

**Output:**
```
=== Workflow Statistics ===
  Total executions: 25
  Total strategic decisions: 12
  Current workflow: /nse → /r → /design
  Workflow stack depth: 3
  Skills with suggest fields: 58
  Valid transitions: 104
  Total skill invocations: 25
```

### graph - Show skill relationship graph

Display all skill transitions.

```bash
python cli.py graph [--filter <category>]
```

**Example:**
```bash
python cli.py graph
python cli.py graph --filter /nse
```

**Output:**
```
=== Skill Relationship Graph ===
  Skills with suggest fields: 58

Skill Transitions:
  /analyze → /nse, /design, /r
  /design → /nse, /r, /llm-brainstorm
  /nse → /r, /design, /r
  ...

  Total transitions: 104
```

### invoke - Invoke a skill

Execute a skill through the orchestrator.

```bash
python cli.py invoke <skill> [args...]
```

**Example:**
```bash
python cli.py invoke /nse
python cli.py invoke /design key=value
```

## Global Options

### --json - Output in JSON format

Useful for scripting and automation.

```bash
python cli.py --json info /nse
python cli.py --json stats
```

**Output:**
```json
{
  "skill": "/nse",
  "metadata": {
    "name": "nse",
    "description": "Next Step Engine v2"
  },
  "suggests": ["/r", "/design"],
  ...
}
```

### --quiet, -q - Suppress info messages

Only show errors and critical information.

```bash
python cli.py --quiet stats
```

### --verbose, -v - Enable verbose output

Show detailed error information with stack traces.

```bash
python cli.py --verbose info /invalid-skill
```

### --version - Show version

```bash
python cli.py --version
```

## Exit Codes

- **0** - Success
- **1** - Error (invalid input, operation failed)
- **130** - Cancelled by user (Ctrl+C)

## Examples

### Check what to do after running /nse

```bash
python cli.py suggest /nse
```

### Plan a workflow starting from /design

```bash
python cli.py workflow /design --depth 3
```

### Validate a proposed workflow

```bash
python cli.py validate "/nse,/r,/design,/r"
```

### Get skill information for documentation

```bash
python cli.py info /nse
```

### Export statistics to JSON for analysis

```bash
python cli.py --json stats > stats.json
```

### View recent activity

```bash
python cli.py history --limit 10
```

### Check all available skill transitions

```bash
python cli.py graph
```

## Troubleshooting

### Git Bash Path Issues

If you see errors like `Skill 'C:/Program Files/Git/nse' not found`, Git Bash is interpreting `/nse` as a Windows path.

**Solution 1:** Use double slashes
```bash
python cli.py suggest //nse
```

**Solution 2:** Disable path conversion
```bash
MSYS_NO_PATHCONV=1 python cli.py suggest /nse
```

**Solution 3:** Use the wrapper script
```bash
./orchestrator.sh suggest nse
```

### Skill Not Found

If you get "Skill not found" errors:

1. Check the skill name is correct
2. Use the `graph` command to see all available skills
3. Skills without suggest fields won't appear in suggestions

### Invalid Workflow

If workflow validation fails:

1. Use `suggest <skill>` to see valid next skills
2. Use `workflow <skill>` to see all possible paths
3. Check that transitions exist in the graph output

## Integration with Python

The CLI can also be imported and used programmatically:

```python
from orchestrator import main

# Run CLI programmatically
exit_code = main()
```

Or use the orchestrator directly:

```python
from orchestrator import master_orchestrator

# Get suggestions
suggestions = master_orchestrator.get_workflow_suggestions('/nse')

# Validate workflow
validation = master_orchestrator.validate_workflow(['/nse', '/r', '/design'])

# Get statistics
stats = master_orchestrator.get_workflow_stats()
```
