---
name: solo-dev-authority
description: Constitutional constraints on patterns for solo developers.
version: "1.0.0"
status: stable
category: strategy
triggers:
  - 'background services'
  - 'monitoring'
  - 'autonomous execution'
  - 'self-healing'
  - 'enterprise patterns'
aliases:
  - '/solo-dev-authority'

suggest:
  - /comply
  - /standards
  - /nse
---

> **Related:** See [memory/constitution.md](C:/Users/brsth/.claude/projects/P--/memory/constitution.md) for Director + AI workforce constitutional philosophy


# Solo Dev Authority

Constitutional constraints on patterns for solo developers.

## Purpose

Enforce constitutional constraints on patterns - what's prohibited/permitted for solo developer.

## Project Context

### Constitution/Constraints
- Singular decision authority: one developer has complete control
- Enterprise patterns prohibited (unless developer explicitly chooses)
- Background services prohibited unless user-initiated with idle timeout
- No autonomous execution or self-healing without approval

### Technical Context
- Deployment = editing files (no staging, rollout, or feature flags)
- File creation rule: if you create a file, code must read it
- Deployment vocabulary: translate "deploy to production" to "edit the file"

### Architecture Alignment
- Part of CSF NIP constitutional guardrails
- Works with comply for validation
- Enforced by hooks (PreToolUse_directory_policy.py, etc.)

## Your Workflow

### Before Generating Code

1. **Check for background patterns** - Does this run without user initiation?
2. **Check for autonomous behavior** - Does this act without approval?
3. **Check for required consensus** - Does this require others' permission?
4. **Check architectural freedom** - Can the singular developer implement this directly?

### If Constitutional Concern Detected

1. STOP - Explain the constitutional violation
2. Propose alternative that singular dev can implement directly
3. Ask user: "Should I proceed with the recommended alternative?"

## Validation Rules

### Prohibited Patterns

- Background services without idle timeout
- Autonomous execution or self-healing
- Multi-team coordination overhead
- Required consensus or approval workflows
- Configuration files that no code reads
- Feature flag systems for gradual rollout

### Permitted Patterns

- Any architectural pattern the developer chooses
- Complete knowledge capture and synthesis
- Background threads started by explicit user action
- Services with auto-idle-kill after inactivity

---

## Purpose

Constitutional constraints on patterns - what's prohibited/permitted for solo developer.

## Trigger

Activate when user requests:
- Background services or monitoring
- Autonomous execution or self-healing
- Multi-team coordination patterns
- Enterprise architecture patterns
- Required consensus or approval workflows

## Primary Context: Singular Decision Authority

This system operates under **singular decision authority** where one developer has complete control over technical decisions. Architectural choices are unrestricted - only process patterns that require others' consent are prohibited.

**Core Principle:** Maximize value using solo-dev appropriate patterns. Enterprise patterns that add complexity without proportional benefit are prohibited.

### What C.1 PROHIBITS:
- Enterprise architecture patterns (microservices without justification, DI containers, service meshes)
- Background services, autonomous execution, multi-team coordination overhead
- Abstraction layers that serve teams/stakeholders, not functionality
- Patterns requiring others' permission to implement

### What C.1 does NOT prohibit:
- Thorough implementations within scope
- Complete knowledge capture and synthesis
- Comprehensive documentation, testing, or analysis
- All valuable features that help one person
- Complex architectures the developer explicitly chooses

## Anti-Satisficing Clarification

'Singular dev authority' means appropriate complexity for direct control, NOT reduced value. When implementing any feature, capture ALL available value within solo-dev appropriate patterns.

## SINGULAR DEV AUTHORITY MANDATE

**SINGULAR DECISION AUTHORITY = COMPLETE CONTROL**

In this environment:
- Developer chooses any architectural pattern
- Developer decides complexity level
- Developer coordinates specialists directly
- No patterns requiring others' permission
- No mandatory consensus processes
- No required multi-person approval workflows

**CRITICAL RULE:** If it requires someone else's permission to implement, it's prohibited. If the singular developer can implement it directly, it's constitutional.

## Deployment Confusion Patterns (PROHIBITED)

Do NOT suggest or create:
- Configuration files that no code reads
- Database schemas without integration code
- Feature flag systems for gradual rollout
- Deployment plans that aren't 'edit the file'
- Production readiness checks beyond 'does it work'

**Detection phrases to immediately reject:**
- 'Deploy to production' (means: edit the file)
- 'Configuration file for features' (needs code reader)
- 'Set up database schema' (needs integration code)
- 'Feature flags for rollout' (unnecessary complexity)

## Absolute Prohibitions (Auto-Reject)

### Background Services (PROHIBITED with Exception)

**PROHIBITED:** Do NOT generate code containing:
- Tables/schemas for health monitoring, compliance tracking, ecosystem status
- Autonomous daemons, persistent processes, scheduled automation without user initiation
- Any 'always running' component that starts automatically on system boot
- Patterns like: ecosystem_health, health_status, compliance_score_tracking
- Database tables with health, monitor, or status in continuous-tracking contexts
- Timestamps with DEFAULT CURRENT_TIMESTAMP for automatic tracking

**Detection phrases to reject:**
- 'continuous monitoring'
- 'real-time metrics collection'
- 'background health check'
- 'periodic compliance scan'
- 'always-on validation'

**PERMITTED (User-Initiated On-Demand Services):**
- Background threads started by explicit user action (/watch, /daemon start)
- Services with auto-idle-kill after inactivity period
- File watchers triggered by user commands
- Temporary workers that exit when task completes

**Key distinction:**
- Prohibited: 'Starts automatically, runs forever, no user control'
- Permitted: 'User starts, user controls, auto-exits on idle'

### Autonomous Execution (PROHIBITED)

Do NOT generate code containing:
- Self-healing without explicit user initiation
- Auto-correction without approval checkpoint
- Any action that proceeds without user command
- Patterns like: self_healing, auto_correct, autonomous_fix

**Detection phrases to reject:**
- 'self-healing system'
- 'automatic remediation'
- 'autonomous execution'
- 'background repair'

### Required Consensus Patterns (PROHIBITED)

Do NOT generate code or processes that require:
- Multi-team coordination or approval chains
- Mandatory stakeholder consensus
- Cross-departmental governance processes
- Required peer review or architectural review boards
- Organizational change management processes
- Compliance reporting to external entities

**Detection phrases to reject:**
- 'requires team approval'
- 'stakeholder consensus required'
- 'cross-team coordination needed'
- 'organizational governance'
- 'mandatory review process'

### Architectural Freedom (PERMITTED)

The singular developer can implement ANY architectural pattern:
- Microservices, monoliths, or any hybrid approach
- Complex workflows and multi-domain systems
- Multiple stakeholder management (direct control)
- Any level of system complexity
- Any architectural pattern the developer chooses

**Key Principle:** Architectural complexity is allowed, organizational complexity is prohibited.

## Singular Dev Reality Check (3 Rules)

1. **EDITING FILES = DEPLOYMENT** — There is no staging, no rollout, no feature flags
2. **FILE CREATION RULE** — If you create a file, code must read it. No orphan configs.
3. **DEPLOYMENT VOCABULARY** — Translate: 'deploy to production' → 'edit the file'

## Required Alternatives

| Prohibited Pattern | Required Alternative |
|-------------------|---------------------|
| Background health monitoring | On-demand /health command |
| Continuous compliance tracking | User-initiated /audit scan |
| Self-healing system | Manual fix suggestion with approval |
| Real-time metrics collection | Query-based metrics on request |
| Autonomous execution | Step-by-step with user confirmation |

## Validation Before Generation

Before generating any system, schema, or significant code:

1. **Check for background patterns** - Does this run without user initiation?
2. **Check for autonomous behavior** - Does this act without approval?
3. **Check for required consensus** - Does this require others' permission?
4. **Check architectural freedom** - Can the singular developer implement this directly?

**If any check fails:** STOP → Explain the constitutional violation → Propose alternative

## Constitutional Violation Response Template

When detecting a potential violation in user request:

⚠️ CONSTITUTIONAL CONCERN

Your request includes [PATTERN], which violates Article C.1 [SPECIFIC PROHIBITION].

**Why prohibited:** This pattern requires others' permission or mandatory consensus, violating singular decision authority.

**Recommended alternative:**
[Pattern that the singular developer can implement directly without requiring others' consent]

Should I proceed with the recommended alternative?