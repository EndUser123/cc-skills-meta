# PHASE 1.6.5: Intentional Exception Registry

**When this applies:**
- Package has known deviations from plugin standards
- You want gitready to stop flagging those violations on subsequent runs

**Why this matters:** Intentional deviations (e.g., `src/` in established brownfield packages) should be documented so gitready doesn't repeatedly flag them as violations.

## Step 1: Check for Exceptions File

```powershell
$exceptionsFile = "$TARGET_DIR/.gitready/exceptions.json"

if (Test-Path $exceptionsFile) {
    $exceptions = Get-Content $exceptionsFile | ConvertFrom-Json
    Write-Host "Found exceptions file with $($exceptions.exceptions.Count) registered exceptions"
} else {
    Write-Host "No exceptions file found"
}
```

## Step 2: Load Exceptions Schema

```json
{
  "exceptions": [
    {
      "path": "src/",
      "violation": "src/ directory not in plugin spec",
      "reason": "Established brownfield package - src/ predates plugin migration",
      "waived_until": "2027-01-01"
    },
    {
      "path": "pyproject.toml",
      "violation": "pyproject.toml forbidden in plugins",
      "reason": "Required for pip install compatibility during transition period",
      "waived_until": null
    }
  ],
  "package_version": "1.0.0",
  "created": "2026-03-26"
}
```

**Schema fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `path` | Yes | Path relative to package root (e.g., `src/`, `pyproject.toml`) |
| `violation` | Yes | Description of the standards violation |
| `reason` | Yes | Why this deviation is intentional/necessary |
| `waived_until` | No | ISO date string. If null, never expires. If set, re-prompt after date |
| `created` | Auto | When the exception was created |
| `package_version` | Auto | Version when exception was created |

## Step 3: Validate Exceptions

```powershell
if (Test-Path $exceptionsFile) {
    $exceptions = Get-Content $exceptionsFile | ConvertFrom-Json

    foreach ($exc in $exceptions.exceptions) {
        $fullPath = Join-Path $TARGET_DIR $exc.path
        if (-not (Test-Path $fullPath)) {
            Write-Host "Warning: Exception path no longer exists: $($exc.path)"
            Write-Host "   Consider removing this exception on next run"
        }

        if ($exc.waived_until) {
            $expDate = [DateTime]::Parse($exc.waived_until)
            if ($expDate -lt (Get-Date)) {
                Write-Host "Warning: Exception expired: $($exc.path) (expired $($exc.waived_until))"
                Write-Host "   Re-evaluate whether this exception should remain"
            }
        }
    }
}
```

## Step 4: Generate Exceptions File (If Needed)

```powershell
# If violations found but no exceptions file exists, offer to create one
if (-not (Test-Path $exceptionsFile) -and $VIOLATIONS_FOUND) {
    Write-Host ""
    Write-Host "Violations detected but no exceptions file found."
    Write-Host "Would you like to create .gitready/exceptions.json to document intentional deviations?"
    Write-Host ""
    Write-Host "This prevents gitready from repeatedly flagging these as violations."
    Write-Host "Example:"
    Write-Host '  { "exceptions": [{ "path": "src/", "violation": "...", "reason": "...", "waived_until": null }] }'
    Write-Host ""
    # User confirms, then create file
}
```

**Exception file location:** `.gitready/exceptions.json` in the package root
