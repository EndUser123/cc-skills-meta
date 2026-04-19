---
name: ocpa
description: Optimal Completion Path Analysis for architectural decision validation
version: 1.0.0
status: stable
category: architecture
triggers:
  - /ocpa
aliases:
  - /ocpa

suggest:
  - /nse
  - /design
  - /r
---

# OCPA - Optimal Completion Path Analysis

Validate architectural decisions through optimal completion path analysis.

## Purpose

Validate architectural decisions through optimal completion path analysis.

## Project Context

### Constitution/Constraints
- Spec compliance: Follow architecture decisions
- Investigation before recommendations: Verify actual tradeoffs

### Technical Context
- Main documentation: `P:/__csf/src/csf/cli/nip/ocpa.md`
- Evaluates completion paths for architectural alternatives

### Architecture Alignment
- Integrates with /design for decision framework
- Supports /r for solution optimization

## Your Workflow

1. Receive architectural decision query
2. Identify completion paths for each alternative
3. Analyze effort, risk, and value for each path
4. Recommend optimal path with reasoning

## Validation Rules

- MUST analyze actual completion paths, not theoretical
- MUST provide reasoning for recommendations
- DO NOT skip tradeoff analysis

## Quick Start

```bash
/ocpa "microservices vs monolith"
```

## Main Documentation

`P:/__csf/src/csf/cli/nip/ocpa.md`
