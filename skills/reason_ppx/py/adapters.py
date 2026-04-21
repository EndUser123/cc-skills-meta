from __future__ import annotations
import time

from .config import OrchestratorConfig
from .models import ExternalQuery, ExternalResult
from .normalizer import normalize_external_result
from .providers import call_provider


def execute_external_queries(queries: list[ExternalQuery], config: OrchestratorConfig) -> list[ExternalResult]:
    results: list[ExternalResult] = []
    deadline = time.monotonic() + config.soft_deadline_seconds
    min_success = config.min_success_for_quorum

    successful_results: list[ExternalResult] = []

    for q in queries:
        # Check soft deadline: if time's up and we have quorum, stop waiting
        if len(successful_results) >= min_success and time.monotonic() >= deadline:
            remaining = ExternalResult(
                role=q.role,
                provider=q.provider,
                ok=False,
                stderr="Skipped: quorum satisfied before reaching this provider.",
                error_type="quorum_satisfied",
                elapsed_ms=0,
                arrived=False
            )
            results.append(remaining)
            continue

        # Check hard deadline
        if time.monotonic() >= deadline + (config.hard_deadline_seconds - config.soft_deadline_seconds):
            remaining = ExternalResult(
                role=q.role,
                provider=q.provider,
                ok=False,
                stderr="Skipped: hard deadline exceeded.",
                error_type="hard_deadline",
                elapsed_ms=0,
                arrived=False
            )
            results.append(remaining)
            continue

        provider_cfg = config.provider_configs.get(q.provider)
        if not provider_cfg or not provider_cfg.enabled:
            results.append(ExternalResult(
                role=q.role,
                provider=q.provider,
                ok=False,
                stderr="Provider disabled.",
                error_type="disabled",
                elapsed_ms=0,
                arrived=True
            ))
            continue

        attempt = 0
        last_result = None
        while attempt <= provider_cfg.retries:
            result = call_provider(q)
            result = normalize_external_result(result, config)
            last_result = result

            if result.ok:
                successful_results.append(result)
                break

            # Structured hook-error interrupts
            if result.error_type == "attach_console":
                result.stderr = f"HOOK_INTERRUPT: {result.provider} failed with console attachment error."
                break

            transient = result.error_type in {"rate_limit", "empty_output"}
            if not transient:
                break

            # Exponential backoff
            if attempt < provider_cfg.retries:
                backoff = min(
                    config.backoff_base_seconds * (2 ** attempt),
                    config.backoff_max_seconds
                )
                time.sleep(backoff)
            attempt += 1

        if last_result is not None:
            results.append(last_result)
        else:
            results.append(ExternalResult(
                role=q.role,
                provider=q.provider,
                ok=False,
                stderr="No result obtained.",
                error_type="no_result",
                elapsed_ms=0,
                arrived=True
            ))

    return results
