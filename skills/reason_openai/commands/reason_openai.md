---
name: reason_openai
description: Elite reasoning ecosystem — adversarial split, implementation realism, and decision compression across 5 layers. Triggers when user asks to reason, decide, critique, analyze, or think through a complex problem.
argument-hint: <mode> [options]
allowed-tools: Skill
---

# /reason_openai

Invokes the **reason_openai** skill — elite reasoning with adversarial split, implementation realism, and decision compression.

## Direct skill delegation

```
Skill("reason_openai:reason_openai", args="{{*}}")
```

## Mode flags

| Flag | Purpose |
|------|---------|
| `--mode decide --force-choice` | Stuck decision — force a recommendation |
| `--mode review --depth board` | High-stakes critique with full board review |
| `--mode execute --ship` | Move from thought to action |
| `--mode off --depth deep` | Vague discomfort — exploratory |
| `--kill` | Aggressive pruning of options |
| `--invert` | Failure path analysis |

## When to use

- Complex decisions with competing priorities
- Architecture or migration reviews
- Post-mortems and pre-mortems
- Strategy vs. tactician conflicts

## Examples

```
/reason_openai this migration plan feels too neat
/reason_openai --mode decide --force-choice postgres vs clickhouse for this workload
/reason_openai --mode execute --ship I have too many competing priorities this week
/reason_openai --mode review --depth board review this architecture for hidden failure modes
```
