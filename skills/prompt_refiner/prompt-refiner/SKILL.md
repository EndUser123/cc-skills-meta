---
name: prompt-refiner
description: Executable prompt specification system with constitutional compliance and cognitive techniques
category: strategy
triggers:
  - /prompt-refiner
aliases:
  - /prompt-refiner
---

# Prompt Refiner v14.0

Meta-prompt system for high-reliability LLM systems with executable specifications and constitutional compliance.

**Main Implementation:** `P:/__csf/src/csf/cli/nip/prompt_refiner.md`

## Quick Start

```bash
/prompt-refiner analyze "your prompt here"      # Analyze and refine
/prompt-refiner triage "task description"       # Rapid triage routing
/prompt-refiner template                        # Show triage template
```

## Rapid Triage

Answer three questions to route to appropriate cognitive technique:

**Q1: Reversibility?**
- 1.0-1.25 (trivial) → MIN-EFFORT: CoT only
- 1.5-1.75 (moderate) → STANDARD: ToT + Self-Consistency
- 2.0 (irreversible) → MAXIMUM-SAFETY: Multi-Agent + Full Matrix

**Q2: Dependencies?**
- 0-1 → Chain-of-Thought
- 2-4 → Tree-of-Thoughts + Self-Consistency
- 5+ → Multi-Agent Debate

**Q3: Evidence available?**
- YES → Tier 1 ceiling 95%
- NO → Tier 3 ceiling 75%
- UNCERTAIN → Tier 4 ceiling 50%

## Cognitive Techniques

- **Chain-of-Thought** - For trivial reversibility, low dependencies
- **Tree-of-Thoughts** - For moderate complexity with self-consistency checking
- **Multi-Agent Debate** - For high complexity and irreversible operations
