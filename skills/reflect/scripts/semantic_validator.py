#!/usr/bin/env python3
"""Semantic validation layer for regex-detected signals.

This module provides a validation layer that uses AI to filter false positives
from regex-detected learning signals. It wraps semantic_detector.py to validate
HIGH and MEDIUM confidence signals before they reach user review.

Key features:
- validate_signal(): Validate a single regex-detected signal
- validate_signals_batch(): Validate multiple signals in parallel
- Confidence-based filtering to reduce noise
"""

from typing import Any

from semantic_detector import semantic_analyze


def validate_signal(signal: dict[str, Any], model: str | None = None) -> dict[str, Any]:
    """
    Validate a regex-detected signal using semantic AI analysis.

    Args:
        signal: Dictionary with signal data:
            - content (str): The signal content
            - confidence (float): Regex detection confidence (0.0-1.0)
            - pattern_type (str): Type of pattern that matched (e.g., "correction")
        model: Optional model override for semantic analysis

    Returns:
        Dictionary with validation result:
            - status (str): "validated" | "rejected" | "error"
            - original_confidence (float): Original regex confidence
            - semantic_confidence (float | None): AI confidence if available
            - reason (str): Explanation for the validation result
            - extracted_learning (str | None): Clean learning statement if validated
    """
    content = signal.get("content", "")
    original_confidence = signal.get("confidence", 0.0)

    # Call semantic analyzer
    result = semantic_analyze(content, model=model)

    # Handle errors (timeout, CLI not found, etc.)
    if result is None:
        return {
            "status": "error",
            "original_confidence": original_confidence,
            "semantic_confidence": None,
            "reason": "Semantic analysis failed (timeout or CLI unavailable)",
            "extracted_learning": None,
        }

    # Extract semantic analysis results
    is_learning = result.get("is_learning", False)
    semantic_confidence = result.get("confidence", 0.0)
    reasoning = result.get("reasoning", "")
    extracted_learning = result.get("extracted_learning")

    # Validate or reject based on semantic analysis
    if is_learning and semantic_confidence >= 0.6:
        return {
            "status": "validated",
            "original_confidence": original_confidence,
            "semantic_confidence": semantic_confidence,
            "reason": reasoning,
            "extracted_learning": extracted_learning,
        }
    else:
        return {
            "status": "rejected",
            "original_confidence": original_confidence,
            "semantic_confidence": semantic_confidence,
            "reason": reasoning,
            "extracted_learning": None,
        }


def validate_signals_batch(
    signals: list[dict[str, Any]],
    model: str | None = None,
    min_confidence: float = 0.6,
    original_confidence_threshold: float = 0.5,
) -> list[dict[str, Any]]:
    """
    Validate multiple signals in batch.

    Args:
        signals: List of signal dictionaries
        model: Optional model override for semantic analysis
        min_confidence: Minimum semantic confidence to validate (default 0.6)
        original_confidence_threshold: Minimum original confidence to process
                                      (default 0.5 - skip LOW confidence signals)

    Returns:
        List of validation results with same length as input signals
    """
    results = []

    for signal in signals:
        original_confidence = signal.get("confidence", 0.0)

        # Skip LOW confidence signals to save API calls
        if original_confidence < original_confidence_threshold:
            results.append(
                {
                    "status": "rejected",
                    "original_confidence": original_confidence,
                    "semantic_confidence": None,
                    "reason": f"Below confidence threshold ({original_confidence_threshold})",
                    "extracted_learning": None,
                }
            )
            continue

        # Validate HIGH/MEDIUM confidence signals
        result = validate_signal(signal, model=model)

        # Apply min_confidence filter
        if result["status"] == "validated":
            semantic_conf = result.get("semantic_confidence", 0.0)
            if semantic_conf < min_confidence:
                # Reject due to low semantic confidence
                results.append(
                    {
                        "status": "rejected",
                        "original_confidence": original_confidence,
                        "semantic_confidence": semantic_conf,
                        "reason": f"Below semantic confidence threshold ({min_confidence})",
                        "extracted_learning": None,
                    }
                )
            else:
                results.append(result)
        else:
            results.append(result)

    return results
