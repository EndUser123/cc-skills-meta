---
name: standards
description: Read and enforce CSF NIP standards
version: "1.0.0"
status: stable
enforcement: strict
category: standards
triggers:
  - /standards
aliases:
  - /standards

suggest:
  - /init
  - /csf-nip-dev
---

# CSF NIP Standards

Read and enforce CSF NIP standards.

## Purpose

Read and enforce CSF NIP development standards.

## Project Context

### Constitution/Constraints
- Follow P:/__csf/docs/standards_inst.md for authoritative standards
- CSF NIP ecosystem has specific development patterns
- Standards are constitutional, not optional

### Technical Context
- Standards document: P:/__csf/docs/standards_inst.md
- Enforced via comply skill
- Integrates with csf-nip-dev for detailed patterns

### Architecture Alignment
- Part of CSF NIP standards system
- Works with comply, csf-nip-dev skills
- Enforced by various hooks

## Your Workflow

When invoked:
1. Read P:/__csf/docs/standards_inst.md
2. Identify relevant standards for current task
3. Apply standards to code/implementation
4. Validate compliance

## Validation Rules

- Standards from standards_inst.md are authoritative
- No deviation without explicit user approval
- Document any exceptions required

---

## Execution

When invoked, read P:/__csf/docs/standards_inst.md and enforce CSF NIP standards.

## Reference

See: P:/__csf/docs/standards_inst.md
