from __future__ import annotations
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import OrchestratorConfig
from .models import ExternalQuery, ExternalResult
from .normalizer import normalize_external_result
from .providers import call_provider


def _call_one(query: ExternalQuery, config: OrchestratorConfig) -> ExternalResult:
    """Execute a single provider call with retries, in a background thread."""
    provider_cfg = config.provider_configs.get(query.provider)
    if not provider_cfg or not provider_cfg.enabled:
        return ExternalResult(
            role=query.role,
            provider=query.provider,
            ok=False,
            stderr="Provider disabled.",
            error_type="disabled",
            elapsed_ms=0,
            arrived=True
        )

    attempt = 0
    last_result = None
    while attempt <= provider_cfg.retries:
        result = call_provider(query)
        result = normalize_external_result(result, config)
        last_result = result

        if result.ok:
            return result

        transient = result.error_type in {"rate_limit", "empty_output"}
        if not transient:
            return result

        if attempt < provider_cfg.retries:
            backoff = min(
                config.backoff_base_seconds * (2 ** attempt),
                config.backoff_max_seconds
            )
            time.sleep(backoff)
        attempt += 1

    if last_result is not None:
        return last_result
    return ExternalResult(
        role=query.role,
        provider=query.provider,
        ok=False,
        stderr="No result obtained.",
        error_type="no_result",
        elapsed_ms=0,
        arrived=True
    )


def execute_external_queries(queries: list[ExternalQuery], config: OrchestratorConfig) -> list[ExternalResult]:
    """Fire all external calls in parallel, collect until soft_deadline, then return."""
    start_time = time.monotonic()
    deadline = start_time + config.soft_deadline_seconds
    hard_deadline = start_time + config.hard_deadline_seconds
    min_success = config.min_success_for_quorum

    results_map: dict[str, ExternalResult] = {}
    completed_providers: set[str] = set()

    # Fire all calls in parallel threads
    with ThreadPoolExecutor(max_workers=len(queries)) as executor:
        future_to_query = {
            executor.submit(_call_one, q, config): q
            for q in queries
        }

        for future in as_completed(future_to_query):
            query = future_to_query[future]
            elapsed = time.monotonic() - start_time

            # If we've passed the hard deadline, cancel remaining futures
            if elapsed >= hard_deadline:
                for f in future_to_query:
                    f.cancel()
                break

            # Collect result if we still have time
            if elapsed < hard_deadline:
                try:
                    result = future.result()
                    results_map[query.provider] = result
                    completed_providers.add(query.provider)

                    # Quorum satisfied: cancel remaining
                    if result.ok and len([r for r in results_map.values() if r.ok]) >= min_success:
                        for f in future_to_query:
                            if not f.done():
                                f.cancel()
                        break

                except Exception as e:
                    results_map[query.provider] = ExternalResult(
                        role=query.role,
                        provider=query.provider,
                        ok=False,
                        stderr=f"EXCEPTION: {e}",
                        error_type="exception",
                        elapsed_ms=int((time.monotonic() - start_time) * 1000),
                        arrived=True
                    )

    # Build ordered results list matching query order
    ordered_results: list[ExternalResult] = []
    for q in queries:
        if q.provider in results_map:
            ordered_results.append(results_map[q.provider])
        else:
            # Not reached due to hard deadline
            ordered_results.append(ExternalResult(
                role=q.role,
                provider=q.provider,
                ok=False,
                stderr="Skipped: hard deadline exceeded.",
                error_type="hard_deadline",
                elapsed_ms=0,
                arrived=False
            ))

    return ordered_results
