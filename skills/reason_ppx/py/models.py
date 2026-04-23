from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskType(str, Enum):
    CODEREVIEW = "codereview"
    PLANNING = "planning"
    BRAINSTORM = "brainstorm"
    RESEARCH = "research"
    DEBUG = "debug"
    REFACTOR = "refactor"
    GENERAL = "general"


class ClaimStatus(str, Enum):
    VERIFIED = "VERIFIED"
    INFERRED = "INFERRED"
    UNPROVEN = "UNPROVEN"


class ExternalRole(str, Enum):
    VERIFY = "verify"
    REDTEAM = "redteam"
    ALTERNATIVE = "alternative"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MissingCapability(str, Enum):
    FRESHNESS = "freshness"
    CITATIONS = "citations"
    ADVERSARIAL_REVIEW = "adversarial_review"
    LONG_HORIZON = "long_horizon"
    MULTIMODAL = "multimodal"
    POLICY_RISK = "policy_risk"


class DataClass(str, Enum):
    LOCAL_ONLY = "local_only"
    LOCAL_OK = "local_ok"
    REDACT_THEN_REMOTE = "redact_then_remote"
    REMOTE_ONLY = "remote_only"


@dataclass
class ClassificationResult:
    task_type: TaskType
    confidence: float
    scores: Dict[str, float] = field(default_factory=dict)
    rationale: str = ""
    missing_capabilities: List[MissingCapability] = field(default_factory=list)


@dataclass
class ContextBundle:
    explicit_paths: List[str] = field(default_factory=list)
    inline_context: str = ""
    detected_code: bool = False
    detected_filesystem_reference: bool = False
    working_summary: str = ""
    data_class: DataClass = DataClass.LOCAL_OK


@dataclass
class Claim:
    id: str
    text: str
    status: ClaimStatus
    impact: Severity
    evidence: List[str] = field(default_factory=list)
    challenged_by: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass
class Finding:
    role: ExternalRole
    provider: str
    summary: str
    severity: Severity
    claims_supported: List[str] = field(default_factory=list)
    claims_challenged: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class ExternalQuery:
    role: ExternalRole
    provider: str
    prompt: str
    timeout_seconds: int = 180


@dataclass
class ExternalResult:
    role: ExternalRole
    provider: str
    ok: bool
    stdout: str = ""
    stderr: str = ""
    normalized: List[Finding] = field(default_factory=list)
    error_type: Optional[str] = None
    elapsed_ms: int = 0
    arrived: bool = False


@dataclass
class ReasoningState:
    query: str
    task: Optional[ClassificationResult] = None
    context: ContextBundle = field(default_factory=ContextBundle)
    primary_frame: str = ""
    challenger_frame: str = ""
    internal_draft: str = ""
    claims: List[Claim] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    external_queries: List[ExternalQuery] = field(default_factory=list)
    external_results: List[ExternalResult] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    final_answer: str = ""
    confidence_summary: str = ""
    strategy_shift: str = ""
    execution_notes: List[str] = field(default_factory=list)
    # Decision flags from CLI
    force_choice: bool = False
    kill: bool = False
    invert: bool = False
    ship: bool = False

    def high_impact_unproven_count(self) -> int:
        return sum(
            1 for c in self.claims
            if c.impact == Severity.HIGH and c.status == ClaimStatus.UNPROVEN
        )
