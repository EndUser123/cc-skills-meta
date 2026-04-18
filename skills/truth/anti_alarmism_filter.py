from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

"""
Anti-Alarmism Filter for Professional Command Output

This module provides comprehensive filtering of alarmist, dramatic, and unprofessional
language from command outputs, ensuring measured, technical communication.

Algorithm Approach:
- Pattern-based detection of alarmist language
- Professional replacement mapping
- Severity assessment based on actual impact
- Context-aware filtering
- Statistical tracking of filtering effectiveness

Author: CSF NIP Implementation Team
Version: 1.0.0 - Professional Language Filter
License: MIT
"""




class LanguageCategory(Enum):
    """Categories of unprofessional language to filter."""

    ALARMISM = "alarmism"                    # Emergency/crisis language
    EXAGGERATION = "exaggeration"           # Overstated impact claims
    EMOTIONAL = "emotional"                  # Emotionally charged words
    DRAMATIC = "dramatic"                    # Theatrical language
    UNCERTAIN_CRISIS = "uncertain_crisis"    # Claims of crisis without evidence
    ABSOLUTE = "absolute"                    # Absolute statements without qualification


class ProfessionalSeverity(Enum):
    """Professional severity levels based on actual impact."""

    LOW = "low"                              # Minor issues, cosmetic problems
    MEDIUM = "medium"                        # Functional issues, performance impact
    HIGH = "high"                            # Significant issues, security concerns
    CRITICAL = "critical"                    # System down, data loss scenarios


@dataclass
class FilterResult:
    """Result of language filtering."""

    original_text: str
    filtered_text: str
    removed_phrases: list[str] = field(default_factory=list)
    categories_detected: list[LanguageCategory] = field(default_factory=list)
    severity_assigned: ProfessionalSeverity | None = None
    confidence_score: float = 0.0
    processing_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LanguagePattern:
    """Pattern for detecting and replacing unprofessional language."""

    category: LanguageCategory
    pattern: str
    replacements: list[str]
    severity_impact: float
    confidence_threshold: float
    context_sensitive: bool = False


class AntiAlarmismFilter:
    """Comprehensive filter for alarmist and unprofessional language."""

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.filter_stats = {
            "total_texts_processed": 0,
            "patterns_matched": 0,
            "replacements_made": 0,
            "categories_detected": {cat.value: 0 for cat in LanguageCategory},
            "severity_assignments": {sev.value: 0 for sev in ProfessionalSeverity}
        }

        # Initialize language patterns
        self.patterns = self._initialize_patterns()
        self.context_rules = self._initialize_context_rules()

    def _initialize_patterns(self) -> list[LanguagePattern]:
        """Initialize language patterns for filtering."""
        patterns = [
            # Alarmism patterns
            LanguagePattern(
                category=LanguageCategory.ALARMISM,
                pattern=r"\bCRITICAL\b(?!\s+SYSTEM\s+DOWN)",
                replacements=["HIGH", "SIGNIFICANT"],
                severity_impact=0.7,
                confidence_threshold=0.8
            ),
            LanguagePattern(
                category=LanguageCategory.ALARMISM,
                pattern=r"\bSYSTEM\s+COLLAPSE\b",
                replacements=["system degradation", "operational issues"],
                severity_impact=0.9,
                confidence_threshold=0.9
            ),
            LanguagePattern(
                category=LanguageCategory.ALARMISM,
                pattern=r"\bEMERGENCY\b",
                replacements=["priority", "important"],
                severity_impact=0.6,
                confidence_threshold=0.7
            ),
            LanguagePattern(
                category=LanguageCategory.ALARMISM,
                pattern=r"\bCRISIS\b",
                replacements=["issue", "concern", "challenge"],
                severity_impact=0.5,
                confidence_threshold=0.6
            ),

            # Exaggeration patterns
            LanguagePattern(
                category=LanguageCategory.EXAGGERATION,
                pattern=r"\bCATASTROPHIC\b",
                replacements=["significant", "serious"],
                severity_impact=0.8,
                confidence_threshold=0.9
            ),
            LanguagePattern(
                category=LanguageCategory.EXAGGERATION,
                replacements=["serious", "impactful"],
                severity_impact=0.7,
                confidence_threshold=0.8
            ),
            LanguagePattern(
                category=LanguageCategory.EXAGGERATION,
                pattern=r"\bCOMPLETE\s+FAILURE\b",
                replacements=["significant issues", "operational problems"],
                severity_impact=0.8,
                confidence_threshold=0.9
            ),
            LanguagePattern(
                category=LanguageCategory.EXAGGERATION,
                pattern=r"\bTOTAL\s+BREAKDOWN\b",
                replacements=["system issues", "degraded operation"],
                severity_impact=0.8,
                confidence_threshold=0.9
            ),

            # Dramatic patterns
            LanguagePattern(
                category=LanguageCategory.DRAMATIC,
                pattern=r"\bIMMEDIATE\s+INTERVENTION\b",
                replacements=["prompt attention required", "priority action"],
                severity_impact=0.6,
                confidence_threshold=0.7
            ),
            LanguagePattern(
                category=LanguageCategory.DRAMATIC,
                pattern=r"\bURGENT\s+ACTION\s+REQUIRED\b",
                replacements=["priority action recommended", "attention needed"],
                severity_impact=0.5,
                confidence_threshold=0.6
            ),

            # Absolute patterns
            LanguagePattern(
                category=LanguageCategory.ABSOLUTE,
                pattern=r"\bALWAYS\b",
                replacements=["typically", "generally", "often"],
                severity_impact=0.3,
                confidence_threshold=0.5
            ),
            LanguagePattern(
                category=LanguageCategory.ABSOLUTE,
                pattern=r"\bNEVER\b",
                replacements=["rarely", "infrequently", "seldom"],
                severity_impact=0.3,
                confidence_threshold=0.5
            ),

            # Uncertain crisis patterns
            LanguagePattern(
                category=LanguageCategory.UNCERTAIN_CRISIS,
                pattern=r"\bMAY\s+COLLAPSE\b",
                replacements=["may experience issues", "could face challenges"],
                severity_impact=0.4,
                confidence_threshold=0.7
            ),
        ]

        # Add additional patterns for strict mode
        if self.strict_mode:
            strict_patterns = [
                LanguagePattern(
                    category=LanguageCategory.EXAGGERATION,
                    pattern=r"\bMASSIVE\b",
                    replacements=["large", "significant"],
                    severity_impact=0.4,
                    confidence_threshold=0.6
                ),
                LanguagePattern(
                    category=LanguageCategory.ALARMISM,
                    pattern=r"\bCRITICAL.*\bFAILURE\b",
                    replacements=["significant failure", "major issue"],
                    severity_impact=0.7,
                    confidence_threshold=0.8
                ),
            ]
            patterns.extend(strict_patterns)

        return patterns

    def _initialize_context_rules(self) -> dict[str, list[str]]:
        """Initialize context-specific rules for language assessment."""
        return {
            "system_down_indicators": [
                "system down", "service unavailable", "complete outage",
                "no response", "connection refused", "server error 500"
            ],
            "data_loss_indicators": [
                "data deleted", "data corrupted", "data lost",
                "file deleted", "database corrupted", "backup failed"
            ],
            "security_breach_indicators": [
                "unauthorized access", "security breach", "exploit",
                "vulnerability exploited", "compromise detected"
            ],
            "performance_indicators": [
                "slow response", "high latency", "timeout",
                "performance degradation", "resource exhaustion"
            ]
        }

    async def filter_text(self, text: str, context: dict[str, Any] | None = None) -> FilterResult:
        """Filter unprofessional language from text."""
        original_text = text
        filtered_text = text
        removed_phrases = []
        categories_detected = []
        total_confidence = 0.0
        pattern_count = 0

        # Apply each pattern
        for language_pattern in self.patterns:
            matches = re.finditer(language_pattern.pattern, filtered_text, flags=re.IGNORECASE)

            for match in matches:
                matched_text = match.group()
                removed_phrases.append(matched_text)

                # Choose appropriate replacement
                replacement = self._choose_replacement(
                    language_pattern.replacements,
                    matched_text,
                    filtered_text,
                    context
                )

                # Replace the matched text
                filtered_text = re.sub(
                    language_pattern.pattern,
                    replacement,
                    filtered_text,
                    flags=re.IGNORECASE
                )

                # Track statistics
                if language_pattern.category not in categories_detected:
                    categories_detected.append(language_pattern.category)

                total_confidence += language_pattern.confidence_threshold
                pattern_count += 1

        # Assess professional severity
        severity = self._assess_severity(original_text, context)

        # Calculate confidence score
        confidence_score = total_confidence / max(pattern_count, 1)

        # Update statistics
        self._update_statistics(categories_detected, severity)

        return FilterResult(
            original_text=original_text,
            filtered_text=filtered_text,
            removed_phrases=removed_phrases,
            categories_detected=categories_detected,
            severity_assigned=severity,
            confidence_score=confidence_score
        )

    def _choose_replacement(self, replacements: list[str], matched_text: str,
                          full_text: str, context: dict[str, Any] | None) -> str:
        """Choose the most appropriate replacement based on context."""
        if not replacements:
            return matched_text.lower()

        # Simple selection - could be enhanced with context awareness
        return replacements[0]

    def _assess_severity(self, text: str, context: dict[str, Any] | None) -> ProfessionalSeverity:
        """Assess professional severity based on actual impact indicators."""
        text_lower = text.lower()

        # Check for actual critical indicators
        critical_indicators = self.context_rules.get("system_down_indicators", [])
        data_loss_indicators = self.context_rules.get("data_loss_indicators", [])
        security_indicators = self.context_rules.get("security_breach_indicators", [])
        performance_indicators = self.context_rules.get("performance_indicators", [])

        # Critical severity - system actually down or data lost
        if any(indicator in text_lower for indicator in critical_indicators + data_loss_indicators):
            return ProfessionalSeverity.CRITICAL

        # High severity - security breach or major performance issues
        if any(indicator in text_lower for indicator in security_indicators):
            return ProfessionalSeverity.HIGH

        # Check performance impact if available in context
        if context and "performance_impact" in context:
            perf_impact = context["performance_impact"]
            if perf_impact > 50:  # >50% performance degradation
                return ProfessionalSeverity.HIGH
            if perf_impact > 20:  # >20% performance degradation
                return ProfessionalSeverity.MEDIUM

        # Check for performance indicators in text
        if any(indicator in text_lower for indicator in performance_indicators):
            return ProfessionalSeverity.MEDIUM

        # Default to medium if any issues found, low if no clear indicators
        if any(indicator in text_lower for indicator in ["issue", "problem", "error", "warning"]):
            return ProfessionalSeverity.MEDIUM

        return ProfessionalSeverity.LOW

    def _update_statistics(self, categories_detected: list[LanguageCategory],
                         severity: ProfessionalSeverity):
        """Update filtering statistics."""
        self.filter_stats["total_texts_processed"] += 1
        self.filter_stats["patterns_matched"] += len(categories_detected)

        for category in categories_detected:
            self.filter_stats["categories_detected"][category.value] += 1

        self.filter_stats["severity_assignments"][severity.value] += 1

    def get_statistics(self) -> dict[str, Any]:
        """Get filtering statistics."""
        stats = self.filter_stats.copy()

        # Calculate derived statistics
        if stats["total_texts_processed"] > 0:
            stats["avg_patterns_per_text"] = stats["patterns_matched"] / stats["total_texts_processed"]
        else:
            stats["avg_patterns_per_text"] = 0.0

        # Most common category
        if stats["categories_detected"]:
            stats["most_common_category"] = max(
                stats["categories_detected"].items(),
            )[0]
        else:
            stats["most_common_category"] = None

        return stats

    def reset_statistics(self):
        """Reset filtering statistics."""
        self.filter_stats = {
            "total_texts_processed": 0,
            "patterns_matched": 0,
            "replacements_made": 0,
            "categories_detected": {cat.value: 0 for cat in LanguageCategory},
            "severity_assignments": {sev.value: 0 for sev in ProfessionalSeverity}
        }

    def is_professional_text(self, text: str, threshold: float = 0.8) -> bool:
        """Check if text meets professional standards without filtering."""
        # Count unprofessional indicators
        unprofessional_count = 0
        total_patterns = len(self.patterns)

        for pattern in self.patterns:
            if re.search(pattern.pattern, text, flags=re.IGNORECASE):
                unprofessional_count += 1

        # Calculate professionalism score
        if total_patterns > 0:
            professionalism_score = 1.0 - (unprofessional_count / total_patterns)
        else:
            professionalism_score = 1.0

        return professionalism_score >= threshold

    def get_professional_severity_assessment(self, findings: dict[str, Any]) -> dict[str, Any]:
        """Get professional severity assessment based on actual findings."""
        assessment = {
            "severity": ProfessionalSeverity.LOW,
            "confidence": 0.8,
            "reasoning": [],
            "recommendations": []
        }

        # System actually down
        if findings.get("system_down", False):
            assessment["severity"] = ProfessionalSeverity.CRITICAL
            assessment["confidence"] = 1.0
            assessment["reasoning"].append("System is currently unavailable")
            assessment["recommendations"].append("Immediate system restoration required")

        # Data loss detected
        elif findings.get("data_loss", False):
            assessment["severity"] = ProfessionalSeverity.CRITICAL
            assessment["confidence"] = 0.9
            assessment["reasoning"].append("Data loss detected")
            assessment["recommendations"].append("Data recovery and backup restoration needed")

        # Security breach
        elif findings.get("security_breach", False):
            assessment["severity"] = ProfessionalSeverity.HIGH
            assessment["confidence"] = 0.9
            assessment["reasoning"].append("Security breach detected")
            assessment["recommendations"].append("Security incident response required")

        # High performance impact
        elif findings.get("performance_impact", 0) > 50:
            assessment["severity"] = ProfessionalSeverity.HIGH
            assessment["confidence"] = 0.8
            assessment["reasoning"].append(f'Performance impact: {findings["performance_impact"]}%')
            assessment["recommendations"].append("Performance optimization required")

        # Moderate performance impact
        elif findings.get("performance_impact", 0) > 20:
            assessment["severity"] = ProfessionalSeverity.MEDIUM
            assessment["confidence"] = 0.7
            assessment["reasoning"].append(f'Performance impact: {findings["performance_impact"]}%')
            assessment["recommendations"].append("Performance monitoring and optimization")

        # Security issues present
        elif findings.get("security_issues", 0) > 5:
            assessment["severity"] = ProfessionalSeverity.HIGH
            assessment["confidence"] = 0.8
            assessment["reasoning"].append(f'Security issues found: {findings["security_issues"]}')
            assessment["recommendations"].append("Security audit and remediation needed")

        elif findings.get("security_issues", 0) > 0:
            assessment["severity"] = ProfessionalSeverity.MEDIUM
            assessment["confidence"] = 0.7
            assessment["reasoning"].append(f'Security issues found: {findings["security_issues"]}')
            assessment["recommendations"].append("Security review recommended")

        # Default low severity with monitoring recommendation
        else:
            assessment["reasoning"].append("No critical issues detected")
            assessment["recommendations"].append("Continue monitoring")

        return assessment

    def export_configuration(self, file_path: Path):
        """Export current filter configuration to file."""
        config = {
            "strict_mode": self.strict_mode,
            "patterns": [
                {
                    "category": p.category.value,
                    "pattern": p.pattern,
                    "replacements": p.replacements,
                    "severity_impact": p.severity_impact,
                    "confidence_threshold": p.confidence_threshold,
                    "context_sensitive": p.context_sensitive
                }
                for p in self.patterns
            ],
            "context_rules": self.context_rules,
            "statistics": self.get_statistics()
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, default=str)

    def import_configuration(self, file_path: Path):
        """Import filter configuration from file."""
        with open(file_path, encoding="utf-8") as f:
            config = json.load(f)

        self.strict_mode = config.get("strict_mode", False)

        # Rebuild patterns from features.config
        self.patterns = []
        for pattern_config in config.get("patterns", []):
            pattern = LanguagePattern(
                category=LanguageCategory(pattern_config["category"]),
                pattern=pattern_config["pattern"],
                replacements=pattern_config["replacements"],
                severity_impact=pattern_config["severity_impact"],
                confidence_threshold=pattern_config["confidence_threshold"],
                context_sensitive=pattern_config.get("context_sensitive", False)
            )
            self.patterns.append(pattern)

        # Update context rules
        self.context_rules = config.get("context_rules", self.context_rules)