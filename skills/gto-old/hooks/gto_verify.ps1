# GTO Verification Stop Hook (PowerShell)
#
# Windows-native fallback when bash is not available.
# Blocks session exit (exit 2) until GTO assertions pass.
# Exit 0: Verification passed, session can end
# Exit 2: Verification failed, must retry

$ErrorActionPreference = "Stop"

# Get terminal ID from first argument or environment
# Skill-based hooks receive terminal_id as argument from wrapper
# Settings-based hooks use CLAUDE_TERMINAL_ID environment variable
$RawTerminal = if ($args.Count -gt 0) { $args[0] } else { $env:CLAUDE_TERMINAL_ID }
if ([string]::IsNullOrEmpty($RawTerminal)) {
    Write-Host '{"decision": "block", "reason": "Terminal ID not provided. Multi-terminal isolation requires unique terminal ID."}'
    exit 2
}

$ProjectRoot = $env:CLAUDE_PROJECT_DIR
if ([string]::IsNullOrEmpty($ProjectRoot)) {
    $ProjectRoot = "."
}

# Sanitize terminal_id: only allow alphanumeric, dash, underscore; max 64 chars
# This prevents path injection (SEC-001) and shell injection (SEC-002)
$TerminalId = ($RawTerminal -replace '[^a-zA-Z0-9_-]', '') -replace '(?<=^.{64}).*', ''
if ([string]::IsNullOrEmpty($TerminalId)) {
    Write-Host '{"decision": "block", "reason": "TERMINAL_ID contains no valid characters after sanitization. Must contain alphanumeric, dash, or underscore only."}'
    exit 2
}

# Path to assertions script
$AssertionsScript = ".claude/skills/gto/evals/gto-assertions.py"

# GTO Scope Guard: Only run assertions if GTO artifacts exist
$StateDir = Join-Path $ProjectRoot ".evidence\gto-state-$TerminalId"
if (-not (Test-Path $StateDir -PathType Container)) {
    # No state directory = /gto was never run in this terminal
    Write-Host "GTO scope guard: No GTO state found, skipping verification."
    exit 0
}

# Check for recent artifacts (within last 2 hours)
$RecentArtifacts = Get-ChildItem -Path $StateDir -Filter "*.md" -Recurse:$false |
    Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-2) } |
    Measure-Object |
    Select-Object -ExpandProperty Count

if ($RecentArtifacts -eq 0) {
    # No recent artifacts = /gto hasn't run recently
    Write-Host "GTO scope guard: No recent GTO artifacts found, skipping verification."
    exit 0
}

# Run assertions with timeout (prevent hangs)
# Using 30 second timeout to match Claude Code's own timeout conventions
$SessionStart = (Get-Date).ToString("o")
$ProcessInfo = New-Object System.Diagnostics.ProcessStartInfo
$ProcessInfo.FileName = "python"
$ProcessInfo.Arguments = "`"$AssertionsScript`" --terminal `"$TerminalId`" --project-root `"$ProjectRoot`" --session-start `"$SessionStart`""
$ProcessInfo.UseShellExecute = $false
$ProcessInfo.RedirectStandardOutput = $true
$ProcessInfo.RedirectStandardError = $true

$Process = New-Object System.Diagnostics.Process
$Process.StartInfo = $ProcessInfo
$Process.Start() | Out-Null

# Wait for completion with 30 second timeout
if ($Process.WaitForExit(30000)) {
    $AssertionOutput = $Process.StandardOutput.ReadToEnd()
    $AssertionExit = $Process.ExitCode
} else {
    $Process.Kill()
    $AssertionOutput = "Assertion script timeout after 30 seconds"
    $AssertionExit = 1
}

if ($AssertionExit -eq 0) {
    Write-Host "GTO verification passed. Session complete."
    Write-Host $AssertionOutput
    exit 0
} else {
    # Assertions failed - block session exit
    $BlockMessage = @{
        decision = "block"
        reason = "GTO assertions failed. Run manually: python $AssertionsScript --terminal $TerminalId --project-root $ProjectRoot"
    } | ConvertTo-Json

    Write-Host "GTO assertions failed. Run manually:"
    Write-Host "python $AssertionsScript --terminal $TerminalId --project-root $ProjectRoot"
    Write-Host ""
    Write-Host "Last output:"
    Write-Host $AssertionOutput
    Write-Host $BlockMessage
    exit 2
}
