@echo off
REM Stop hook that triggers reflection when enabled
REM Windows batch file version

setlocal EnableDelayedExpansion

REM Use P: drive paths for CSF package
set "SKILL_DIR=P:\.claude\skills\reflect"
set "STATE_FILE=%SKILL_DIR%\.state\auto-reflection.json"
set "LOCK_FILE=%SKILL_DIR%\.state\reflection.lock"
set "LOG_FILE=P:\.claude\reflect-hook.log"

REM Log function
call :log "Stop hook triggered"

REM Check if auto-reflection is enabled
if not exist "%STATE_FILE%" (
    call :log "State file not found, allowing stop"
    exit /b 0
)

REM Check if enabled using PowerShell
for /f "delims=" %%a in ('powershell -Command "try { $data = Get-Content '%STATE_FILE%' -Raw | ConvertFrom-Json; $data.enabled } catch { 'False' }"') do set "ENABLED=%%a"

if not "%ENABLED%"=="True" (
    call :log "Auto-reflection disabled, allowing stop"
    exit /b 0
)

REM Check for stale lock (>10 minutes = 600 seconds)
if exist "%LOCK_FILE%" (
    REM Get file age in seconds using PowerShell
    for /f "delims=" %%a in ('powershell -Command "$file = Get-Item '%LOCK_FILE%'; [int](Get-Date).Subtract($file.LastWriteTime).TotalSeconds"') do set "LOCK_AGE=%%a"

    if !LOCK_AGE! LSS 600 (
        call :log "Recent lock exists (age: !LOCK_AGE!s), skipping"
        exit /b 0
    )

    call :log "Removing stale lock (age: !LOCK_AGE!s)"
    del "%LOCK_FILE%"
)

REM Create lock
type nul > "%LOCK_FILE%"
call :log "Lock created"

REM Get transcript path from stdin
set /p INPUT=
set "TRANSCRIPT_PATH="
for /f "delims=" %%a in ('echo %INPUT% ^| powershell -Command "$input = $input [Console]::In.ReadToEnd() ^| ConvertFrom-Json; $input.transcript_path"') do set "TRANSCRIPT_PATH=%%a"

call :log "Transcript path: %TRANSCRIPT_PATH%"

REM Run reflection in background using PowerShell Start-Process
call :log "Starting background reflection"
powershell -Command "Start-Process powershell -ArgumentList '-NoProfile', '-Command', '& { $env:TRANSCRIPT_PATH=''%TRANSCRIPT_PATH%''; $env:AUTO_REFLECTED=''true''; python ''%SKILL_DIR%\scripts\reflect.py'' 2>&1; Remove-Item ''%LOCK_FILE%''; exit }' -WindowStyle Hidden"

call :log "Background process spawned, allowing stop"
exit /b 0

REM Log subroutine
:log
echo [%DATE% %TIME%] %~1 >> "%LOG_FILE%"
exit /b
