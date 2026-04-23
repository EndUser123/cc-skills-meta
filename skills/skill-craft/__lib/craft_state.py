from dataclasses import dataclass, field
from typing import Optional

@dataclass
class FidelityScore:
    trigger_accuracy: float
    outcome_accuracy: float
    degradation_delta: float
    passed: bool
    details: dict = field(default_factory=dict)

@dataclass
class CertGateResult:
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

@dataclass
class CraftState:
    phase: str
    exit_condition: bool = False
    loop_count: int = 0
    fidelity_score: Optional[FidelityScore] = None
    cert_gate: Optional[CertGateResult] = None
    all_findings: list[dict] = field(default_factory=list)
    execution_results: dict = field(default_factory=dict)
