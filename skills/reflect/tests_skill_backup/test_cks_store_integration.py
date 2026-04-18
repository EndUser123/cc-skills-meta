#!/usr/bin/env python3
"""Integration tests for CKS schema integration into store_to_cks()."""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path("P:/__csf").resolve()))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

try:
    from scripts.cks_schema_mapper import CKSMetadata, ConfidenceLevel, FindingType
except ImportError:

    class FindingType:
        PATTERN = "PATTERN"
        REFACTOR = "REFACTOR"
        DEBT = "DEBT"
        DOC = "DOC"
        OPT = "OPT"

    class ConfidenceLevel:
        HIGH = "HIGH"
        MEDIUM = "MEDIUM"
        LOW = "LOW"

    class CKSMetadata:
        def __init__(self, finding_type, severity_weight, category_confidence):
            self.finding_type = finding_type
            self.severity_weight = severity_weight
            self.category_confidence = category_confidence


try:
    from src.core.retrospective_common import store_to_cks
except ImportError:
    store_to_cks = None


def test_store_to_cks_calls_classify_finding_type():
    """Test that store_to_cks calls classify_finding_type."""
    if store_to_cks is None:
        assert False, "store_to_cks() not imported"

    text = "Consider using caching"
    category = "optimization"
    score = 8

    with patch("scripts.cks_schema_mapper.classify_finding_type") as mock_classify:
        with patch("knowledge.systems.cks.unified.ingest_pattern") as mock_ingest:
            mock_classify.return_value = CKSMetadata(FindingType.OPT, 0.6, ConfidenceLevel.HIGH)
            mock_ingest.return_value = "cks_entry_123"

            result = store_to_cks(text=text, category=category, score=score)

            mock_classify.assert_called_once_with(category)
            call_kwargs = mock_ingest.call_args[1]
            assert "metadata" in call_kwargs
            metadata = call_kwargs["metadata"]
            assert "finding_type" in metadata
            assert metadata["finding_type"] == FindingType.OPT


def test_store_to_cks_adds_cks_metadata_to_finding():
    """Test that CKS metadata is added to finding."""
    if store_to_cks is None:
        assert False, "store_to_cks() not imported"

    text = "Consider using caching"
    category = "optimization"
    score = 8

    with patch("scripts.cks_schema_mapper.classify_finding_type") as mock_classify:
        with patch("knowledge.systems.cks.unified.ingest_pattern") as mock_ingest:
            mock_classify.return_value = CKSMetadata(FindingType.OPT, 0.6, ConfidenceLevel.HIGH)
            mock_ingest.return_value = "cks_entry_123"

            result = store_to_cks(text=text, category=category, score=score)

            call_kwargs = mock_ingest.call_args[1]
            metadata = call_kwargs.get("metadata", {})
            assert "finding_type" in metadata
            assert "severity_weight" in metadata
            assert "category_confidence" in metadata
            assert metadata["finding_type"] == FindingType.OPT
            assert metadata["severity_weight"] == 0.6
            assert metadata["category_confidence"] == ConfidenceLevel.HIGH


def test_store_to_cks_multiple_findings_all_mapped():
    """Test that multiple findings all get mapped correctly."""
    if store_to_cks is None:
        assert False, "store_to_cks() not imported"

    test_findings = [
        {
            "text": "Use caching",
            "category": "optimization",
            "score": 8,
            "expected_type": FindingType.OPT,
            "expected_weight": 0.6,
            "expected_conf": ConfidenceLevel.HIGH,
        },
        {
            "text": "Forgot edge case",
            "category": "forgotten",
            "score": 7,
            "expected_type": FindingType.PATTERN,
            "expected_weight": 0.7,
            "expected_conf": ConfidenceLevel.HIGH,
        },
        {
            "text": "Extract magic numbers",
            "category": "code quality",
            "score": 6,
            "expected_type": FindingType.REFACTOR,
            "expected_weight": 0.5,
            "expected_conf": ConfidenceLevel.MEDIUM,
        },
        {
            "text": "Missing validation",
            "category": "violation",
            "score": 9,
            "expected_type": FindingType.DEBT,
            "expected_weight": 0.8,
            "expected_conf": ConfidenceLevel.HIGH,
        },
        {
            "text": "Update README",
            "category": "documentation",
            "score": 5,
            "expected_type": FindingType.DOC,
            "expected_weight": 0.4,
            "expected_conf": ConfidenceLevel.MEDIUM,
        },
    ]

    with patch("scripts.cks_schema_mapper.classify_finding_type") as mock_classify:
        with patch("knowledge.systems.cks.unified.ingest_pattern") as mock_ingest:
            mock_ingest.return_value = "cks_entry_xyz"

            for finding in test_findings:
                mock_classify.return_value = CKSMetadata(
                    finding_type=finding["expected_type"],
                    severity_weight=finding["expected_weight"],
                    category_confidence=finding["expected_conf"],
                )
                result = store_to_cks(
                    text=finding["text"], category=finding["category"], score=finding["score"]
                )

            assert mock_classify.call_count == 5
            assert mock_ingest.call_count == 5

            for i, finding in enumerate(test_findings):
                call_args = mock_ingest.call_args_list[i]
                metadata = call_args[1]["metadata"]
                assert metadata.get("finding_type") == finding["expected_type"]
                assert metadata.get("severity_weight") == finding["expected_weight"]
                assert metadata.get("category_confidence") == finding["expected_conf"]


def test_store_to_cks_fallback_on_unstructured_yaml_on_error():
    """Test fallback to unstructured YAML when classify_finding_type fails."""
    if store_to_cks is None:
        assert False, "store_to_cks() not imported"

    text = "Consider using caching"
    category = "optimization"
    score = 8

    with patch("scripts.cks_schema_mapper.classify_finding_type") as mock_classify:
        with patch("knowledge.systems.cks.unified.ingest_pattern") as mock_ingest:
            mock_classify.side_effect = Exception("Classification service unavailable")
            mock_ingest.return_value = "cks_entry_fallback"

            result = store_to_cks(text=text, category=category, score=score)

            assert mock_ingest.called
            assert result == "cks_entry_fallback"
            call_kwargs = mock_ingest.call_args[1]
            metadata = call_kwargs.get("metadata", {})
            assert "finding_type" not in metadata
            assert "severity_weight" not in metadata
            assert "category_confidence" not in metadata


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main([__file__, "-v"]))
