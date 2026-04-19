---
name: pace
description: Cognitive load and WIP tracking for solo dev throttle
version: 1.0.0
status: stable
category: wellness
triggers:
  - /pace
  - "cognitive load"
  - "am I overloaded"
  - "take a break"
aliases:
  - /pace

suggest:
  - /health-monitor
  - /cooldown
  - /q
---

# /pace – Cognitive Load & WIP Tracking

## Purpose

Track cognitive load, WIP, rework, and system health to decide whether to:
- Continue normally.
- Constrain work (smaller changes, mandatory gates).
- Stop or park work and run cooldown/closure.

## When to Use

- At the start of a work block.
- After long or intense sessions.
- When you feel scattered, tired, or tempted to "just do one more big change".

## Inputs

- Optional free-text context:
  - e.g., "I've been at this for 3 hours", "I keep thrashing", "I feel fine".
- Implicit:
  - Session start time and activity log.
  - Git status/log.
  - Recent `/guard` or `/ship` outcomes.

## Dependencies

- Skills:
  - `/health-monitor` – system health, memory, DB, API checks.
- Data:
  - Session activity tracker (duration, operations count).
  - Git CLI (branches, uncommitted files, recent commits).
  - Task list (if available).
  - Recent `/guard` and `/ship` reports (if any).

## High-Level Behavior

### 1. Signal Collection
- **Session duration**: Now - first event / last cooldown
- **WIP**:
  - Number of modified files
  - Number of active branches
  - Count of open tasks for this session/project
- **Rework**:
  - Count of recent "fix"/"revert" commits
  - Recent `/guard` issue counts/severity (if available)
- **System health** via `/health-monitor`:
  - Memory usage levels
  - Hook health
  - DB health
  - API key health

### 2. Load Scoring
Compute a simple score:
- **Low load** – short session, low WIP, low rework, healthy system
- **Medium load** – moderate WIP, some rework, possibly rising memory
- **High load** – long session, high WIP, multiple reverts/fixes, issues from `/health-monitor`

### 3. Behavior Routing
- **For Low**:
  - Recommend continuing; maybe suggest a future `/pace` checkpoint
- **For Medium**:
  - Recommend:
    - Smaller commits
    - Running `/guard` on significant changes
    - Avoiding new major features
- **For High**:
  - Recommend:
    - Stop starting new risky work
    - Run `/cooldown` and/or checkpoint with a small commit
    - If user insists on proceeding, suggest mandatory `/guard` and reduced scope

### 4. Action Recommendations
Provide 2–3 concrete actions:
- e.g., "Commit current work and run /cooldown", "Split this into a smaller slice and run `/guard` before continuing"

## Output Format

- "Pace report" containing:
  - Load level (Low/Medium/High).
  - Key contributing signals (duration, WIP, rework, system health).
  - 2–3 specific recommended next actions.

## Notes

- Keep output short and directive.
- Never force action; always present clear options.
