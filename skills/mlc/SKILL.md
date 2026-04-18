---
name: mlc
description: Minimal Lossy Compaction - Conservative token optimization that preserves most information while dropping redundancy
version: 2.0.0
status: stable
category: optimization
triggers:
  - /mlc
  - "optimize tokens"
  - "reduce verbosity"
  - "condense this"
aliases:
  - /mlc
suggest:
  - /lmc
  - /gto
  - /r
workflow_steps:
  - analyze_token_usage: Measure tokens in target content
  - identify_inefficiencies: Find redundancy, verbosity, waste
  - suggest_optimizations: Propose lossless improvements
  - generate_compact_version: Condensed but complete
  - verify_equivalence: Ensure no information lost
---

# /mlc - Minimal Lossy Compaction

## Purpose

Conservative token optimization that preserves ALL critical information while removing obvious redundancy. Identifies inefficiencies in code, documentation, or output and suggests specific optimizations (20-40% savings).

## When to Use

- **Verbose code**: Functions with excessive comments or冗余 logic
- **Bloated docs**: Documentation that repeats information
- **Inefficient output**: Skill returns that could be more concise
- **Token optimization**: Reducing context usage while preserving meaning

## Project Context

### Constitution/Constraints
- **Solo-dev patterns**: Direct optimization, no team review needed
- **Evidence-based**: Only suggest changes with clear token savings
- **Conservative**: When in doubt, preserve over condense

### Technical Context
- Token efficiency matters for context limits
- Verbose code/docs consume unnecessary capacity
- Skills can generate more efficient output
- Preservation of meaning is non-negotiable

## Your Workflow

1. **Analyze Target Content**: Read file/output, measure tokens, identify structure
2. **Detect Inefficiencies**: Find redundancy, verbosity, repetitive patterns
3. **Generate Optimizations**: Condense while preserving all information
4. **Apply Changes**: Update code/docs/output (if approved)
5. **Verify Equivalence**: Confirm meaning preserved, measure savings

## Validation Rules

### Prohibited Actions

- Do NOT remove information that adds unique value
- Do NOT condense beyond semantic equivalence
- Do NOT optimize without measuring actual token impact
- Do NOT sacrifice clarity for brevity

### Required Preservation

All MLC optimizations MUST preserve:
- **Semantic meaning**: Information content unchanged
- **Critical details**: No loss of nuance or precision
- **Functionality**: Code behavior preserved
- **Citations**: Links and references retained

## Usage

```bash
# Analyze a file for optimization opportunities
/mlc path/to/file.py

# Analyze current conversation output
/mlc --conversation

# Suggest optimizations only (dry run)
/mlc --dry-run path/to/file.md

# Apply optimizations automatically
/mlc --apply path/to/file.py
```

## Output Format

```
=== MLC Analysis: target.py ===
Current tokens: 1,234
Potential savings: ~234 tokens (19%)

Inefficiencies Found:
1. [25 tokens] Redundant comments at lines 15-20
   → Comment repeats what code already states
   → Suggestion: Remove or condense to key insight only

2. [89 tokens] Duplicate error handling in functions
   → Same try/except pattern repeated 4x
   → Suggestion: Extract to helper function

3. [120 tokens] Verbose docstring with examples
   → 50-line docstring for simple function
   → Suggestion: Condense to 5-10 lines, keep essential info

Optimized Version:
[Show condensed version that preserves all information]

Apply these changes? (--apply flag to auto-confirm)
```

## Common Optimization Patterns

| Pattern | Before | After | Savings |
|---------|--------|-------|---------|
| **Self-evident comments** | `# Increment x` | (removed) | 100% |
| **Duplicate logic** | 4x similar blocks | 1 helper function | 75% |
| **Verbose prose** | 5 sentences | 1-2 sentences | 60-80% |
| **Redundant explanation** | Repeated concept | Reference earlier | 100% |
| **Example-heavy docs** | 10 examples | 2-3 key examples | 80-90% |

## Examples

### Code Optimization
```python
# BEFORE: 89 tokens
def process_data(data):
    # This function takes the data parameter and processes it
    # by iterating through each item and performing operations
    result = []
    for item in data:
        result.append(item * 2)
    return result

# AFTER: 47 tokens (47% savings)
def process_data(data):
    """Double each item in data."""
    return [item * 2 for item in data]
```

### Documentation Optimization
```markdown
# BEFORE: 234 tokens
## Configuration File

The configuration file is used to store configuration settings
for the application. It is located in the config directory and
is named config.yaml. You can edit this file to change settings.

# AFTER: 78 tokens (67% savings)
## Configuration

Settings stored in `config/config.yaml`. Edit to modify application behavior.
```

## Integration with /gto

/gto may suggest `/mlc` when it detects:
- Files with excessive token-to-functionality ratio
- Documentation with redundant sections
- Code patterns that could be consolidated
- Output that exceeds typical token budgets

## Related Skills

- **/lmc**: Lossy Maximal Compaction (drops non-essential content)
- **/gto**: Gap analysis (detects inefficiencies)
- **/r**: Remember/refine (optimization suggestions)
