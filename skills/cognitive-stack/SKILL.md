---
name: cognitive_stack
description: Cognitive-Stack Framework management and orchestration command
category: orchestration
version: 1.0.0
status: stable
triggers:
  - /cognitive-stack
aliases:
  - /cognitive-stack

suggest:
  - /nse
  - /analyze

# Note: /cognitive-frameworks is deprecated - all cognitive frameworks are now
# automatic via cognitive_enhancers hook. No manual invocation needed.
---

# Cognitive-Stack Framework Management

Cognitive-Stack Framework management and orchestration system.

## Purpose

Manage Cognitive-Stack Framework lifecycle including start, stop, restart, status, and configuration.

## Project Context

### Constitution/Constraints
- **User Control** - All framework operations are user-initiated
- **Solo-Dev Appropriate** - No enterprise background services without idle timeout

### Technical Context
- Framework lifecycle management (start, stop, restart)
- Health monitoring and status checks
- Profile-based configuration
- Graceful shutdown support

### Architecture Alignment
- Works with `/nse`, `/analyze`
- Orchestrates cognitive enhancement capabilities
- Note: Cognitive frameworks (Cynefin, Hanlon's Razor, Inversion, Chesterton's Fence,
  Devil's Advocate) are now applied automatically via cognitive_enhancers hook

## Your Workflow

### `status`
1. Check framework process state
2. Display health metrics
3. Show current configuration

### `start [--profile <profile>]`
1. Load profile configuration
2. Initialize framework components
3. Start with specified profile

### `stop [--graceful]`
1. If graceful: signal shutdown, wait for completion
2. If not graceful: terminate immediately
3. Report shutdown status

### `restart`
1. Execute stop sequence
2. Wait for complete shutdown
3. Execute start sequence

### `configure`
1. Open configuration file
2. Display current settings
3. Allow modifications

## Validation Rules

### Prohibited Actions

- Do NOT start framework without verifying profile exists
- Do NOT force kill without graceful option
- Do NOT assume framework state without checking

## Usage

```bash
/cognitive-stack <action> [options]
```

## Actions

### `status`
Show current framework status and health.

**Example:**
```bash
/cognitive-stack status
```

### `start [--profile <profile>]`
Start the Cognitive-Stack framework with optional profile.

**Example:**
```bash
/cognitive-stack start --profile production
```

### `stop [--graceful]`
Stop the framework gracefully or immediately.

**Example:**
```bash
/cognitive-stack stop --graceful
```

### `restart`
Restart the framework.

**Example:**
```bash
/cognitive-stack restart
```

### `configure`
Open framework configuration.

**Example:**
```bash
/cognitive-stack configure
```

## Features

- Framework lifecycle management
- Health monitoring
- Profile-based configuration
- Graceful shutdown support
