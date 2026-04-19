---
name: constraints
description: Show active project constraints from CLAUDE.md
category: project
version: 1.0.0
status: stable
triggers:
  - /constraints
aliases:
  - /constraints

suggest:
  - /comply
  - /standards
  - /nse
---

# /constraints — Show Project Constraints

Displays active constraints extracted from CLAUDE.md.

## Purpose

Display active project constraints extracted from CLAUDE.md constitution, providing quick reference for behavioral rules and technical standards.

## Project Context

### Constitution/Constraints
- **Evidence-First** - Show actual constraints from CLAUDE.md, not summaries
- **Truthfulness > Agreement** - Display constraints accurately, even if they limit options

### Technical Context
- Loads constraints from `P:/CLAUDE.md`
- Extracts via `src.constraints.load_constraints()`
- Returns structured constraint data

### Architecture Alignment
- Works with `/comply`, `/standards`, `/nse`
- Reference for constitutional compliance

## Your Workflow

1. Load CLAUDE.md file
2. Extract constraint sections
3. Parse structured constraint data
4. Display constraints with categories:
   - TDD requirements
   - Python version
   - Linting/formatting standards
   - Testing requirements
   - Other project-specific constraints

## Validation Rules

### Prohibited Actions

- Do NOT display constraints without reading CLAUDE.md
- Do NOT summarize constraints - show actual content
- Do NOT guess constraint values

## Quick Start

```python
from src.constraints import load_constraints

constraints = load_constraints(Path("P:/"))
print(f"TDD Required: {constraints.tdd_required}")
print(f"Python Version: {constraints.python_version}")
```
