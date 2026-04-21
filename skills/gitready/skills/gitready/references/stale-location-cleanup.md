# PHASE 1.8: Stale Location Cleanup and Junction/Symlink Setup

**When this applies:**
- Package type is `claude-skill`, `claude-plugin`, or `brownfield-plugin`
- Package has skills (SKILL.md) or hooks (scripts/hooks/*.py)
- Old stale locations exist at canonical paths (`P:/.claude/skills/` or `P:/.claude/hooks/`)

**Why this matters:** The packages directory is now the source of truth. Old canonical locations create dual implementations that cause confusion and stale code.

## PRE-CHECK: Guard Against Running on Stale Locations

**CRITICAL**: Before doing anything, detect if the input path is itself a stale install location:

```powershell
# If invoked against P:/.claude/skills/{name}, auto-resolve to P:/packages/{name}
$inputPath = "P:/INVOKED_PATH"  # from gitready argument
$skillName = Split-Path $inputPath -Leaf

if ($inputPath -match "^P:/\\.claude/skills/") {
    Write-Host "WARNING: gitready was invoked on an installed skill location."
    Write-Host "The source of truth should be at P:/packages/$skillName"
    Write-Host ""
    Write-Host "Auto-resolving to source location..."
    $resolvedSource = "P:/packages/$skillName"
    if (-not (Test-Path $resolvedSource)) {
        Write-Host "ERROR: No package found at $resolvedSource"
        Write-Host "Move the files first: cp -r $inputPath/* $resolvedSource/"
        exit 1
    }
    $TARGET_DIR = $resolvedSource
} else {
    $TARGET_DIR = $inputPath
}
```

**If the source does NOT exist at `P:/packages/{name}`**:
1. Copy files to the packages location: `cp -r {INPUT_PATH}/* P:/packages/{name}/`
2. Remove the stale install location
3. Create the junction at `P:/.claude/skills/{name}` → `P:/packages/{name}`
4. Continue with gitready using the packages path as `TARGET_DIR`

**Rule: Never gitready a stale location without migrating to packages first.**

## Step 1: Detect Package Contents

```powershell
# Identify what this package contains
TARGET_DIR="P:/packages/PACKAGE_NAME"

# Check for skills
if (Test-Path "$TARGET_DIR/skills/*/SKILL.md") {
    $skills = Get-ChildItem "$TARGET_DIR/skills/*/SKILL.md"
    Write-Host "Skills found: $($skills.Count)"
}

if (Test-Path "$TARGET_DIR/skill/SKILL.md") {
    Write-Host "Root skill found at skill/SKILL.md"
}

# Check for hooks
if (Test-Path "$TARGET_DIR/scripts/hooks/*.py") {
    $hooks = Get-ChildItem "$TARGET_DIR/scripts/hooks/*.py"
    Write-Host "Hooks found: $($hooks.Count)"
}
```

## Step 2: Detect Stale Skill Locations

```powershell
# Check if skill exists at old canonical location
# Pattern: P:/.claude/skills/PACKAGE_NAME or P:/.claude/skills/SKILL_NAME
$packageName = "PACKAGE_NAME"

# Check for stale junction or directory at canonical skill path
$canonicalSkillPath = "P:/.claude/skills/$packageName"
if (Test-Path $canonicalSkillPath) {
    $item = Get-Item $canonicalSkillPath
    if ($item.LinkType -eq "Junction" -or $item.FullName -ne (Resolve-Path "$TARGET_DIR/skills/$packageName" -ErrorAction SilentlyContinue).Path) {
        Write-Host "STALE: Skill exists at canonical path but points elsewhere"
    }
}
```

## Step 3: Detect Stale Hook Symlinks

```powershell
# Check for broken symlinks in hooks directory
cd P:/.claude/hooks
Get-ChildItem -Force | Where-Object { $_.LinkType -eq "SymbolicLink" } | ForEach-Object {
    $target = $_.Target
    if (-not (Test-Path $target)) {
        Write-Host "BROKEN SYMLINK: $_ -> $target"
    }
}
```

## Step 4: Clean Up Stale Skill Locations

```powershell
# DELETE old stale skill directory/junction at canonical path
$canonicalSkillPath = "P:/.claude/skills/$packageName"
if (Test-Path $canonicalSkillPath) {
    # Check if it's actually stale (not pointing to our new package)
    $item = Get-Item $canonicalSkillPath
    $targetPath = if ($item.LinkType) { $item.Target } else { $item.FullName }

    if (-not $targetPath.StartsWith("P:\packages\$packageName")) {
        Write-Host "Removing stale skill at: $canonicalSkillPath"
        Remove-Item -Force $canonicalSkillPath -Recurse
    }
}
```

## Step 5: Clean Up Stale Hook Symlinks

```powershell
# Remove broken symlinks to old hook paths
cd P:/.claude/hooks
Get-ChildItem -Force | Where-Object {
    $_.LinkType -eq "SymbolicLink" -and
    ($_.Target -like "*src*" -or -not (Test-Path $_.Target))
} | ForEach-Object {
    Write-Host "Removing stale hook symlink: $_"
    Remove-Item -Force $_.FullName
}
```

## Step 6: Create New Junctions for Skills

After cleanup, create junctions pointing to the NEW package location:

**IMPORTANT**: Sanitize the junction name to remove problematic characters like `@`, `?`, `*`, etc.
These characters cause issues with slash command invocation on Windows.

```powershell
# Junction for skill at root level (skill/SKILL.md)
$packageName = "PACKAGE_NAME"
$targetDir = "P:/packages/$packageName"

# Sanitize junction name - remove characters that cause slash command issues
$junctionName = $packageName -replace '[@?*:<>|+]', ''
if ($junctionName -ne $packageName) {
    Write-Host "NOTE: Sanitized junction name from '$packageName' to '$junctionName'"
}

# Skill at root: skill/SKILL.md -> Junction at P:/.claude/skills/PACKAGE_NAME
if (Test-Path "$targetDir/skill/SKILL.md") {
    New-Item -ItemType Junction -Path "P:/.claude/skills/$junctionName" -Target "$targetDir/skill" -Force
    Write-Host "Created junction: P:/.claude/skills/$junctionName -> $targetDir/skill"
}

# Skill in skills/ subdirectory
if (Test-Path "$targetDir/skills/$packageName/SKILL.md") {
    New-Item -ItemType Junction -Path "P:/.claude/skills/$junctionName" -Target "$targetDir/skills/$packageName" -Force
    Write-Host "Created junction: P:/.claude/skills/$junctionName -> $targetDir/skills/$packageName"
}
```

## Step 7: Create New Symlinks for Hooks

```powershell
# Create symlinks for hook files pointing to scripts/hooks/
$targetDir = "P:/packages/$packageName"
cd P:/.claude/hooks

Get-ChildItem "$targetDir/scripts/hooks/*.py" | ForEach-Object {
    $hookName = $_.Name
    $sourcePath = "$targetDir/scripts/hooks/$hookName"

    # Remove existing symlink if present
    $existingLink = "P:/.claude/hooks/$hookName"
    if (Test-Path $existingLink) {
        Remove-Item -Force $existingLink
    }

    # Create new symlink
    cmd /c "mklink $hookName $sourcePath"
    Write-Host "Created symlink: $hookName -> $sourcePath"
}
```

## Step 8: Verify Setup

```powershell
# Verify skills resolve correctly
Get-ChildItem P:/.claude/skills -Force | Where-Object { $_.LinkType -eq "Junction" } | ForEach-Object {
    if (Test-Path $_.Target) {
        Write-Host "OK: $_ -> $($_.Target)"
    } else {
        Write-Host "BROKEN: $_ -> $($_.Target)"
    }
}

# Verify hooks resolve correctly
Get-ChildItem P:/.claude/hooks -Force | Where-Object { $_.LinkType -eq "SymbolicLink" } | ForEach-Object {
    if (Test-Path $_.Target) {
        Write-Host "OK: $_ -> $($_.Target)"
    } else {
        Write-Host "BROKEN: $_ -> $($_.Target)"
    }
}
```

## Critical Rule

- Source of truth = `P:/packages/PACKAGE_NAME/` (the package)
- Junctions/symlinks point FROM canonical location TO package location
- NEVER have skills/hooks exist in BOTH locations
- NEVER use old canonical location as source

## Post-Relocation Cleanup

**When:** Plugin moved, brownfield conversion done (`src/` to `scripts/`), or paths changed.

### Detect Stale Symlinks in P:/.claude/hooks/

```powershell
cd P:/.claude/hooks
Get-ChildItem -Force | Where-Object { $_.LinkType -eq "SymbolicLink" } | ForEach-Object {
    $target = $_.Target
    if (-not (Test-Path $target)) {
        Write-Host "BROKEN: $_ -> $target"
    }
}
```

### Detect Stale Junctions in P:/.claude/skills/

```powershell
cd P:/.claude/skills
Get-ChildItem -Force | Where-Object { $_.LinkType -eq "Junction" } | ForEach-Object {
    $target = $_.Target
    if (-not (Test-Path $target)) {
        Write-Host "BROKEN: $_ -> $target"
    }
}
```

### Clean Up and Recreate

```powershell
# Remove broken symlinks (hooks)
cd P:/.claude/hooks
Remove-Item -Force hook_name.py  # One per broken symlink

# Remove broken junctions (skills)
cd P:/.claude/skills
Remove-Item -Force "skill-name"  # One per broken junction

# Recreate with correct paths (scripts/hooks/ not src/hooks/)
cd P:/.claude/hooks
cmd /c "mklink hook_name.py P:\packages\PLUGIN_NAME\scripts\hooks\hook_name.py"

# Recreate junctions
New-Item -ItemType Junction -Path "P:\.claude\skills\SKILL_NAME" -Target "P:\packages\PLUGIN_NAME\skills\SKILL_NAME"
```

### Verification After Recreation

```powershell
# Verify symlinks resolve correctly
Get-ChildItem P:/.claude/hooks -Force | Where-Object { $_.LinkType -eq "SymbolicLink" } | ForEach-Object {
    if (Test-Path $_.Target) { Write-Host "OK: $_" } else { Write-Host "STILL BROKEN: $_" }
}

# Verify junctions resolve correctly
Get-ChildItem P:/.claude/skills -Force | Where-Object { $_.LinkType -eq "Junction" } | ForEach-Object {
    if (Test-Path $_.Target) { Write-Host "OK: $_" } else { Write-Host "STILL BROKEN: $_" }
}

# CRITICAL: Verify junction points TO packages/, not FROM packages/
$packageName = "PACKAGE_NAME"
$junction = "P:/.claude/skills/$packageName"
if (Test-Path $junction) {
    $item = Get-Item $junction
    $target = if ($item.LinkType) { $item.Target } else { $item.FullName }
    if ($target -notlike "P:\packages\*") {
        Write-Host "ERROR: Junction points outside packages/ — $target"
        Write-Host "Junction must point TO P:\packages\ not FROM it"
        exit 1
    } else {
        Write-Host "OK: Junction integrity verified — $junction -> $target"
    }
}
```

**CRITICAL PATH RULE:**
- CORRECT: Point to `scripts/hooks/` (after brownfield conversion)
- WRONG: Point to `src/hooks/` (old path before conversion)
