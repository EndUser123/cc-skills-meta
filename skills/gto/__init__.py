"""GTO v3 - Gap/Task/Opportunity Analysis System.

Three-layer architecture:
- Python (deterministic): Data extraction, pattern matching, state management
- Agents/AI (reasoning): Critical thinking, adversarial validation, learning
- Claude (orchestrator): Coordination and output formatting
"""

from __future__ import annotations

__version__ = "3.0.0"

__all__ = [
    # Main orchestrator
    "GTOOrchestrator",
    "OrchestratorConfig",
    "OrchestratorResult",
    "run_gto_analysis",
]

# Import main orchestrator
from .gto_orchestrator import (
    GTOOrchestrator,
    OrchestratorConfig,
    OrchestratorResult,
    run_gto_analysis,
)
