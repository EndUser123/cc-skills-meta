# Agents

This document provides AI-readable context for {{package_name}}.

## What This Package Is

{{description}}

## Package Type

`{{package_type}}` — {{package_type_description}}

## Skills

| Skill | Trigger | Purpose |
|-------|---------|---------|
{{skills_table}}

## Hooks

| Hook | When | Purpose |
|------|------|---------|
{{hooks_table}}

## Commands

| Command | Purpose |
|---------|---------|
{{commands_table}}

## Key Files

| File | Purpose |
|------|---------|
{{key_files_table}}

## Development Setup

```powershell
# Junction (Windows, no admin required)
# Point junction to WHERE SKILL.md lives:
#   - Plugin skills: skills/{skill-name}/SKILL.md → junction target: skills/{skill-name}/
#   - Standalone skills: skill/SKILL.md → junction target: skill/

# Sanitize name (remove @, ?, *, etc.)
$name = "{{package_name}}" -replace '[@?*:<>|+]', ''

New-Item -ItemType Junction -Path "P:\.claude\skills\$name" -Target "P:\packages\{{package_name}}\{{skill_path}}"
```

## Key Constraints

- Solo-dev environment: pragmatic solutions over enterprise patterns
- Plugin structure: `.claude-plugin/` + `scripts/` (NOT `src/`)
- All path references use `CLAUDE_PLUGIN_ROOT` for portability
- Junction target must point to the directory containing SKILL.md

## Workflow

1. `/gitready` — full pipeline on current directory
2. `/gitready <name>` — scaffold new package
3. `/gitready --dry-run` — preview without creating

## Debugging

```powershell
# Check junction resolves correctly
Get-Item "P:\.claude\skills\{{package_name}}" | Select-Object LinkType, Target

# Check hooks directory for broken symlinks
Get-ChildItem P:/.claude/hooks -Force | Where-Object { $_.LinkType -eq "SymbolicLink" -and -not (Test-Path $_.Target) }
```
