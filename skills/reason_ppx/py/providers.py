from __future__ import annotations
import time

from .models import ExternalQuery, ExternalResult
from .utils import run_command


def call_provider(query: ExternalQuery) -> ExternalResult:
    provider = query.provider
    start = time.monotonic()

    if provider == "gemini":
        ok, stdout, stderr = run_command(
            ["gemini", "-y", "-o", "text", query.prompt],
            timeout=query.timeout_seconds
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)
        # attach_console is a non-fatal Windows warning — it doesn't indicate failure
        attach_console_warning = "AttachConsole failed" in stderr
        if attach_console_warning:
            stderr = stderr.replace("AttachConsole failed\n", "")
        if not stdout and ok:
            error_type = "empty_output"
        else:
            error_type = None
        return ExternalResult(
            role=query.role,
            provider=provider,
            ok=ok and bool(stdout),
            stdout=stdout,
            stderr=stderr,
            error_type=error_type,
            elapsed_ms=elapsed_ms,
            arrived=True
        )

    if provider == "pi_m27":
        ok, stdout, stderr = run_command(
            ["pi", "--model", "minimax/MiniMax-M2.7", query.prompt],
            timeout=query.timeout_seconds
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)
        error_type = "rate_limit" if "429" in stderr else None
        return ExternalResult(
            role=query.role,
            provider=provider,
            ok=ok and bool(stdout),
            stdout=stdout,
            stderr=stderr,
            error_type=error_type,
            elapsed_ms=elapsed_ms,
            arrived=True
        )

    if provider == "pi_glm":
        ok, stdout, stderr = run_command(
            ["pi", "--model", "z-ai/glm-5.1", query.prompt],
            timeout=query.timeout_seconds
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)
        error_type = "rate_limit" if "429" in stderr else None
        return ExternalResult(
            role=query.role,
            provider=provider,
            ok=ok and bool(stdout),
            stdout=stdout,
            stderr=stderr,
            error_type=error_type,
            elapsed_ms=elapsed_ms,
            arrived=True
        )

    if provider == "codex":
        ok, stdout, stderr = run_command(
            ["codex", query.prompt],
            timeout=query.timeout_seconds
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return ExternalResult(
            role=query.role,
            provider=provider,
            ok=ok and bool(stdout),
            stdout=stdout,
            stderr=stderr,
            error_type=None if ok else "provider_error",
            elapsed_ms=elapsed_ms,
            arrived=True
        )

    elapsed_ms = int((time.monotonic() - start) * 1000)
    return ExternalResult(
        role=query.role,
        provider=provider,
        ok=False,
        stdout="",
        stderr=f"Unsupported provider: {provider}",
        error_type="unsupported_provider",
        elapsed_ms=elapsed_ms,
        arrived=True
    )
