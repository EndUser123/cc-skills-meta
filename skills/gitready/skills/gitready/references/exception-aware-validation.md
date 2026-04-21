# Exception-Aware Validation (PHASE 1.7)

Before flagging violations, check `.gitready/exceptions.json`:

```powershell
$exceptionsFile = "$TARGET_DIR/.gitready/exceptions.json"

# Load waived paths
$waivedPaths = @()
if (Test-Path $exceptionsFile) {
    $exceptions = Get-Content $exceptionsFile | ConvertFrom-Json
    $now = Get-Date

    foreach ($exc in $exceptions.exceptions) {
        # Skip expired exceptions
        if ($exc.waived_until) {
            $expDate = [DateTime]::Parse($exc.waived_until)
            if ($expDate -lt $now) { continue }
        }
        $waivedPaths += $exc.path
    }
}

# When reporting violations, skip waived ones
foreach ($violation in $violations) {
    if ($waivedPaths -contains $violation.path) {
        Write-Host "WAIVED: $($violation.path) - $($violation.description)"
        continue
    }
    Write-Host "VIOLATION: $($violation.path) - $($violation.description)"
}
```
