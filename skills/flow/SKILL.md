---
name: flow
version: "1.0.0"
status: "stable"
description: Advanced workflow orchestration and pipeline coordination system
category: orchestration
triggers:
  - /flow
aliases:
  - /flow

suggest:
  - /workflow
  - /cwo
  - /nse
---

# Flow Orchestration Command

## Purpose

Advanced workflow orchestration and pipeline coordination system for CSF NIP. Executes workflow sequences, creates/analyzes plans, checks status of running workflows, and validates workflow definitions.

## Project Context

### Constitution / Constraints
- **Solo-dev constraints apply** (CLAUDE.md)
- **No enterprise pipelines**: Simple orchestration, not complex CI/CD
- **State persistence**: Track workflow status across sessions
- **Integration**: Works with planning, research, development, testing tools

### Technical Context
- **Actions**: execute (run workflow), plan (create/analyze), status (check running), validate (verify definitions)
- **Integration points**: Planning module, Research system, Development tools, Testing framework
- **State tracking**: Workflow IDs, status monitoring, persistence
- **Definitions**: YAML workflow files, command-line sequences

### Architecture Alignment
- Integrates with /workflow (workflow management), /cwo (CWO orchestration), /nse (next steps)
- Part of orchestration ecosystem

## Your Workflow

1. **PARSE ACTION** — Detect execute/plan/status/validate from user input
2. **EXECUTE mode** — Run workflow sequence or pipeline with state tracking
3. **PLAN mode** — Create workflow plan from definition (e.g., "research -> design -> implement -> test")
4. **STATUS mode** — Check running workflows, display progress/state
5. **VALIDATE mode** — Verify workflow definition syntax and dependencies
6. **REPORT RESULTS** — Show workflow outcome, errors, or validation issues

## Validation Rules

- **Before execute**: Validate workflow definition first
- **Before reporting**: Parse actual workflow state, don't assume
- **For status**: Check actual running workflows, not cached state
- **Dependencies**: Verify workflow steps can execute in specified order

### Prohibited Actions

- Executing workflows without validation
- Complex enterprise pipeline patterns
- Assuming state without actual verification
- Multi-terminal coordination without state persistence

## Usage

```bash
/flow <action> [options]
```

## Actions

### `execute`
Execute a workflow sequence or pipeline
```bash
/flow execute <workflow> [options]
```

### `plan`
Create or analyze workflow plans
```bash
/flow plan <workflow-definition>
```

### `status`
Check status of running workflows
```bash
/flow status [workflow-id]
```

### `validate`
Validate workflow definitions
```bash
/flow validate <workflow-file>
```

## Examples

```bash
# Execute a planning workflow
/flow execute planning-sequence

# Plan a multi-step development task
/flow plan "research -> design -> implement -> test"

# Check workflow status
/flow status

# Validate workflow definition
/flow validate workflows/deployment.yaml
```

## Integration

Works seamlessly with existing CSF NIP tools:
- Planning module for task decomposition
- Research system for information gathering
- Development tools for implementation
- Testing framework for validation
