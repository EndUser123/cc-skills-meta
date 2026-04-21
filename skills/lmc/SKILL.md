---
name: lmc
description: Lossless Maximal Compaction - Maximum token optimization that preserves all critical information
version: 2.0.0
status: stable
category: optimization
enforcement: advisory
triggers:
  - /lmc
  - "aggressive optimize"
  - "maximal compression"
  - "trim fat"
aliases:
  - /lmc
suggest:
  - /mlc
  - /gto
workflow_steps:
  - analyze_token_usage: Measure tokens in target content
  - identify_essentials: Distinguish must-have from nice-to-have
  - apply_lossy_filters: Drop prose, analysis, verbose output
  - generate_minimal_version: Ultra-compact with core outcomes only
  - verify_functionality: Ensure core behavior/meaning preserved
---

# /lmc - Lossless Maximal Compaction

## Purpose

Maximum token optimization that preserves all critical information while maximizing compression. Keeps function/class signatures and essential logic while removing redundancy.

## When to Use

- **Verbose code**: Functions with excessive documentation
- **Bloated documentation**: Pages that could be paragraphs
- **Inefficient skill output**: Responses that over-explain
- **Maximum compression needed**: Token efficiency over completeness

## Project Context

### Constitution/Constraints
- **Outcome-focused**: Preserve what happened, not how we discussed it
- **Essential-only**: Keep what's necessary, drop helpful but optional
- **Defaults work**: When uncertain, use language/library defaults

### Technical Context
- Code self-documentation is often redundant
- Documentation can be distilled to essentials
- Maximum compression = maximum token efficiency

## Your Workflow

1. **Analyze Target Content**: Read file/output, measure tokens
2. **Identify Essentials**: Distinguish must-have from nice-to-have
3. **Apply Lossy Filters**: Drop prose, analysis, verbose output
4. **Generate Minimal Version**: Ultra-compact with core outcomes only
5. **Add Smart TOC**: For documents 500+ lines, add intent-based quick-nav below the TOC
6. **Verify Functionality**: Ensure core behavior/meaning preserved

### Smart TOC for Large Documents

For documents over 500 lines, add a quick-nav table below the standard TOC:

```markdown
### Quick Navigation by Intent

| I want to... | Go to |
|---|---|
| [intent description] | §Section → Sub-section |
```

**Rules for smart TOC**:
- Maximum 8-10 rows — if more are needed, group by category
- Use section (§N) notation, not line numbers (line numbers rot)
- One specific destination per row, not multi-hop chains
- For single-section docs, skip the smart TOC

## Validation Rules

### Prohibited Actions

- Do NOT drop critical functionality or meaning
- Do NOT remove essential parameters or configuration
- Do NOT optimize code that loses required behavior
- Do NOT drop user requirements or specifications

### Required Preservation

All LMC optimizations MUST preserve:
- **Core functionality**: Code behavior intact
- **Final outcomes**: What the code/doc achieves
- **Critical parameters**: Required configuration
- **Error handling**: Essential error paths

## Usage

```bash
# Aggressively optimize a file
/lmc path/to/file.py

# Aggressively optimize documentation
/lmc path/to/doc.md

# Apply optimizations automatically
/lmc --apply path/to/file.py

# Retention level: decisions-only (default)
/lmc --retain decisions-only path/to/file.py
```

## Output Format

```
=== LMC Analysis: target.py ===
Current tokens: 2,345
Potential savings: ~1,567 tokens (67% - PRESERVED)

Essential Content (PRESERVED):
- Function signatures and behavior
- Core algorithm logic
- Required parameters
- Error handling

Non-Essential Content (DROPPED):
- 450 tokens: Extensive inline comments
- 380 tokens: Verbose docstrings with examples
- 320 tokens: Exploratory comments ("tried X, but...")
- 417 tokens: Redundant variable explanations

Optimized Version:
[Show ultra-compact version with core behavior only]

Apply these changes? (--apply flag to auto-confirm)
```

## Common Optimization Patterns

| Pattern | Before | After | Savings |
|---------|--------|-------|---------|
| **Verbose docstrings** | 30-line explanation | 3-line summary | 90% |
| **Inline comments** | `# i + 1` (every line) | (removed) | 100% |
| **Exploratory prose** | "We tried X but..." | (removed) | 100% |
| **Redundant examples** | 10 usage examples | 1-2 key examples | 80-90% |
| **Self-evident code** | `# Check if x` | (code only) | 100% |

## Retention Levels

| Level | Preserves | Use Case |
|-------|----------|----------|
| **decisions-only** | Final outcomes only | Maximum compression |
| **minimal** | Core functionality | Aggressive optimization |
| **essential** | Required behavior | Conservative optimization |

## Examples

### Code Optimization
```python
# BEFORE: 234 tokens
def process_user_input(user_input):
    """
    Process the user input provided by the user.

    This function takes user_input as a parameter which should be
    a string containing the user's input. It then processes this
    input by validating it...

    Args:
        user_input (str): The input string from the user

    Returns:
        str: The processed input string

    Example:
        >>> process_user_input("hello")
        'HELLO'
    """
    # Validate the input is not empty
    if not user_input:
        return ""
    # Transform to uppercase
    result = user_input.upper()
    return result

# AFTER: 67 tokens (71% savings)
def process_user_input(user_input: str) -> str:
    """Validate and uppercase input."""
    if not user_input:
        return ""
    return user_input.upper()
```

### Documentation Optimization
```markdown
# BEFORE: 567 tokens
## User Authentication Flow

The user authentication flow is a critical component of our
application security infrastructure. When a user attempts to
authenticate, they must provide valid credentials...

[10 paragraphs of explanation]

# AFTER: 89 tokens (84% savings)
## User Authentication

Users authenticate via `/auth/login` with email/password.
Tokens are stored in cookies and validated on each request.
```

## Comparison: MLC vs LMC

| Aspect | MLC (Minimal Lossy) | LMC (Lossless) |
|--------|----------------|-------------|
| **Prose** | Condensed | Removed |
| **Examples** | Key examples retained | Most examples dropped |
| **Comments** | Self-evident ones removed | Almost all removed |
| **Reasoning** | Summarized | Removed |
| **Token Savings** | 20-50% | 60-80% |
| **Risk Level** | Low (meaning preserved) | Medium (some meaning lost) |

## When to Use Each

- **Use /mlc** when: Process matters, rationale needed, documentation critical
- **Use /lmc** when: Only outcome matters, documentation excessive, maximum efficiency needed

## Integration with /gto

/gto may suggest `/lmc` when it detects:
- Severely bloated files (>3x typical size)
- Excessive documentation that obscures content
- Redundant explanations throughout codebase
- Skill output that could be 50%+ shorter
