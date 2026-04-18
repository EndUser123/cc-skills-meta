# Stop hook that triggers reflection when enabled
# Windows PowerShell version

# Use P: drive paths for CSF package
$skillDir = "P:\.claude\skills\reflect"
$stateFile = "$skillDir\.state\auto-reflection.json"
$lockFile = "$skillDir\.state\reflection.lock"
$logFile = "P:\.claude\reflect-hook.log"

# Log function
function Log-Message {
    param([string]$message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$timestamp] $message" | Out-File -FilePath $logFile -Append
}

Log-Message "Stop hook triggered"

# Check if auto-reflection is enabled
if (-not (Test-Path $stateFile)) {
    Log-Message "State file not found, allowing stop"
    exit 0
}

# Read state file
try {
    $state = Get-Content $stateFile -Raw | ConvertFrom-Json
    $enabled = $state.enabled
} catch {
    Log-Message "Failed to read state file: $_"
    $enabled = $false
}

if (-not $enabled) {
    Log-Message "Auto-reflection disabled, allowing stop"
    exit 0
}

# Check for stale lock (>10 minutes = 600 seconds)
if (Test-Path $lockFile) {
    $lockAge = [int](Get-Date).Subtract((Get-Item $lockFile).LastWriteTime).TotalSeconds

    if ($lockAge -lt 600) {
        Log-Message "Recent lock exists (age: ${lockAge}s), skipping"
        exit 0
    }

    Log-Message "Removing stale lock (age: ${lockAge}s)"
    Remove-Item $lockFile -Force
}

# Create lock
New-Item -ItemType File -Path $lockFile -Force | Out-Null
Log-Message "Lock created"

# Get transcript path from stdin
$inputJson = [Console]::In.ReadToEnd()
$transcriptPath = ($inputJson | ConvertFrom-Json).transcript_path

Log-Message "Transcript path: $transcriptPath"

# Run reflection in background
Log-Message "Starting background reflection"

$scriptBlock = {
    param($skillDir, $transcriptPath, $lockFile, $logFile)

    try {
        $env:TRANSCRIPT_PATH = $transcriptPath
        $env:AUTO_REFLECTED = "true"

        & python "$skillDir\scripts\reflect.py" 2>&1 | Out-File -FilePath $logFile -Append

        if ($LASTEXITCODE -eq 0) {
            "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Reflection completed successfully" | Out-File -FilePath $logFile -Append
        } else {
            "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Reflection failed with exit code $LASTEXITCODE" | Out-File -FilePath $logFile -Append
        }
    } finally {
        Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
        "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Lock removed" | Out-File -FilePath $logFile -Append
    }
}

# Start background job
Start-ThreadJob -ScriptBlock $scriptBlock -ArgumentList $skillDir, $transcriptPath, $lockFile, $logFile -Name "ReflectJob" | Out-Null

Log-Message "Background process spawned, allowing stop"
exit 0
