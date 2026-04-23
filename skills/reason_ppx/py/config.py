from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ProviderConfig:
    enabled: bool = True
    timeout_seconds: int = 180
    retries: int = 2


@dataclass
class OrchestratorConfig:
    max_external_rounds: int = 2
    external_on_for_nontrivial: bool = True
    require_verifier_for_research: bool = True
    require_redteam_for_code: bool = True
    classify_confidence_threshold: float = 0.35
    contradiction_threshold: int = 1
    high_impact_claim_threshold: int = 1
    evidence_store_ttl_hours: int = 24  # Widened from default to alleviate deadlock
    provider_configs: Dict[str, ProviderConfig] = field(default_factory=lambda: {
        "gemini": ProviderConfig(enabled=True, timeout_seconds=180, retries=2),
        "pi_m27": ProviderConfig(enabled=True, timeout_seconds=180, retries=2),
        "pi_glm": ProviderConfig(enabled=True, timeout_seconds=180, retries=2),
        "codex": ProviderConfig(enabled=True, timeout_seconds=180, retries=1),
    })
    conceptual_starters: List[str] = field(default_factory=lambda: [
        "what ideas", "brainstorm", "explore", "possibilities", "options", "what could"
    ])
    # Quorum / soft-deadline settings
    soft_deadline_seconds: int = 30
    min_success_for_quorum: int = 1
    hard_deadline_seconds: int = 60
    # Backoff settings
    backoff_base_seconds: float = 1.0
    backoff_max_seconds: float = 8.0
    # Short-output settings
    max_bullets_per_result: int = 6
    max_chars_per_bullet: int = 300
    # CLI overrides (set via --no-external, --mode, --force-choice, --kill, --invert, --ship)
    override_no_external: bool = False
    override_mode: str = "auto"  # auto, review, design, diagnose, optimize, decide, explore, off, execute
    override_force_choice: bool = False
    override_kill: bool = False
    override_invert: bool = False
    override_ship: bool = False
    override_output: str = "compact"  # compact, verbose, json
