---
name: prompt_refiner
description: Executable prompt specification system with constitutional compliance and cognitive techniques
version: 1.0.0
status: stable
category: strategy
triggers:
  - /prompt_refiner
aliases:
  - /prompt_refiner

suggest:
  - /nse
  - /standards
  - /design
---

# Prompt Refiner v14.0

Meta-prompt system for high-reliability LLM systems.

## Purpose

Executable prompt specification system with constitutional compliance and cognitive techniques for high-reliability LLM interactions.

## Project Context

### Constitution/Constraints
- Follows CSF NIP standards for prompt engineering
- Enforces constitutional compliance in all generated prompts
- Cognitive techniques integration for enhanced reasoning

### Technical Context
- Specification: `P:/__csf/docs/prompt_refiner.md`
- Meta-prompt system with tier-based quality levels
- Token-efficient triage for rapid prompt selection

### Architecture Alignment
- Integrates with `/nse` for intelligent recommendations
- Works alongside `/standards` and `/design` for comprehensive workflow

## Your Workflow

1. **Analyze Request**: Determine prompt complexity and requirements
2. **Triage**: Use Q1-Q3 decision matrix for method selection
3. **Apply Template**: Generate prompt using appropriate tier (1.0-2.0)
4. **Validate**: Ensure constitutional compliance and cognitive techniques
5. **Output**: Deliver optimized prompt with quality score

### Triage Questions
- **Q1: Reversibility?** → Determines effort level (MIN-EFFORT to MAXIMUM-SAFETY)
- **Q2: Dependencies?** → Selects reasoning method (CoT, ToT, Multi-Agent)
- **Q3: Evidence?** → Sets confidence tier (95%, 75%, 50%)

## Validation Rules

### Prohibited Actions
- Do not skip triage for complex prompts
- Do not use Tier 4 (50% confidence) for high-stakes decisions
- Do not omit constitutional compliance checks

### Required Outputs
- Quality score for all generated prompts
- Tier justification (evidence type, complexity, reversibility)
- Cognitive technique annotations when applicable

## Quick Start

```bash
/prompt_refiner analyze "your prompt here"
/prompt_refiner triage "task description"
```

## Rapid Triage

### Q1: Reversibility?
- 1.0-1.25: MIN-EFFORT (CoT)
- 1.5-1.75: STANDARD (ToT)
- 2.0: MAXIMUM-SAFETY (Multi-Agent)

### Q2: Dependencies?
- 0-1: Chain-of-Thought
- 2-4: Tree-of-Thoughts + Self-Consistency
- 5+: Multi-Agent Debate

### Q3: Evidence?
- YES: Tier 1 (95%)
- NO: Tier 3 (75%)
- UNCERTAIN: Tier 4 (50%)
