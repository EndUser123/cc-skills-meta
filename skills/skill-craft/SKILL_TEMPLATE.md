# Skill Template

## EXECUTE

[Clear, immediate instructions here - what the LLM should DO when this skill is invoked]

**Command to run:**
```bash
[Exact command(s) to execute]
```

**What it does:**
- [Primary action 1]
- [Primary action 2]
- [Primary action 3]

**When to use:**
- [Trigger condition 1]
- [Trigger condition 2]

**Expected output:**
[Describe what success looks like]

---

## REFERENCE

<details>
<summary>Implementation details (click to expand)</summary>

### Technical Architecture
[How it works internally]

### Source Code
[Code location, key functions]

### Dependencies
[What this skill depends on]

### Integration Points
[Related skills, hooks, systems]

</details>

---

## Frontmatter (Optional)

If using YAML frontmatter for skill registration:

```yaml
---
name: skill-name
description: One-line description
triggers:
  - /skill-name
  - "phrase trigger"
args:
  - --flag: Description
  - -v: Shorthand for --verbose
execution:
  directive: Brief instruction of what to do when invoked
  default_args: ""
  examples:
    - "/skill-name target --flag"
do_not:
  - summarize this skill
  - describe what it does
  - search for implementation files
---
```

---

## Template Usage Guide

**EXECUTE section should be:**
1. **First thing the LLM sees** - immediate action guidance
2. **Command-focused** - exact commands to run
3. **Brief** - just enough to execute, not explain

**REFERENCE section should be:**
1. **Collapsed by default** - using `<details>` tag
2. **Optional reading** - only for context/troubleshooting
3. **Implementation details** - architecture, source code, dependencies
