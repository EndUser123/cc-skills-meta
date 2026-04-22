#!/usr/bin/env python
"""
Extracts learning signals from conversation transcripts.
Identifies corrections, approvals, and patterns with confidence levels.

Supports two detection modes:
- Regex (default): Fast pattern matching, English-focused
- Semantic (--semantic): AI-powered, multi-language, higher accuracy
"""

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

# Import semantic detector (optional)
try:
    from semantic_detector import semantic_analyze

    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False

# Import semantic validator (optional)
try:
    from semantic_validator import validate_signal

    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False

# Import tool error extractor (optional)
try:
    from tool_error_extractor import aggregate_errors, extract_tool_errors

    TOOL_ERROR_AVAILABLE = True
except ImportError:
    TOOL_ERROR_AVAILABLE = False

# Correction patterns (HIGH confidence)
CORRECTION_PATTERNS = [
    r"(?i)no,?\s+don't\s+(?:do|use)\s+(.+?)[,.]?\s+(?:do|use)\s+(.+)",
    r"(?i)actually,?\s+(.+?)\s+(?:is|should be)\s+(.+)",
    r"(?i)instead\s+of\s+(.+?),?\s+(?:you\s+should|use|do)\s+(.+)",
    r"(?i)never\s+(?:do|use)\s+(.+)",
    r"(?i)always\s+(?:do|use|check for)\s+(.+)",
    # German patterns
    r"(?i)nein,?\s+(?:benutze|verwende)\s+(.+?)\s+(?:statt|anstatt)\s+(.+)",
    r"(?i)immer\s+(.+)",
    r"(?i)niemals?\s+(.+)",
]

# Approval patterns (MEDIUM confidence)
APPROVAL_PATTERNS = [
    r"(?i)(?:yes,?\s+)?(?:that's\s+)?(?:perfect|great|exactly|correct)",
    r"(?i)works?\s+(?:perfectly|great|well)",
    r"(?i)(?:good|nice)\s+(?:job|work)",
    # German patterns
    r"(?i)(?:ja,?\s+)?(?:das\s+ist\s+)?(?:perfekt|super|genau|richtig)",
]

# Question patterns (LOW confidence)
QUESTION_PATTERNS = [
    r"(?i)have\s+you\s+considered\s+(.+)",
    r"(?i)why\s+not\s+(?:try|use)\s+(.+)",
    r"(?i)what\s+about\s+(.+)",
    # German patterns
    r"(?i)hast\s+du\s+(?:schon\s+)?(?:an\s+)?(.+)\s+gedacht",
    r"(?i)was\s+ist\s+mit\s+(.+)",
]


def extract_signals(
    transcript_path: str | None = None,
    use_semantic: bool = False,
    semantic_model: str | None = None,
    include_tool_errors: bool = True,
) -> dict[str, list[dict[str, Any]]]:
    """
    Parse transcript and extract learning signals.

    Args:
        transcript_path: Path to transcript file (auto-detected if None)
        use_semantic: Use AI-powered semantic analysis
        semantic_model: Model for semantic analysis (default: haiku)
        include_tool_errors: Enable tool error extraction phase

    Returns:
        Dict of signals grouped by skill name.
    """
    if not transcript_path:
        transcript_path = find_latest_transcript()

    if not transcript_path or not Path(transcript_path).exists():
        print(f"Warning: Transcript not found: {transcript_path}")
        return {}

    signals = []
    messages = load_transcript(transcript_path)
    skills_used = find_skill_invocations(messages)

    # Extract user messages for analysis
    user_messages = []
    for i, msg in enumerate(messages):
        if msg.get("role") == "user":
            user_messages.append(
                {
                    "index": i,
                    "content": str(msg.get("content", "")),
                    "context": messages[max(0, i - 5) : i + 1],
                }
            )

    # Phase 1: Regex-based detection (fast)
    for user_msg in user_messages:
        content = user_msg["content"]
        context = user_msg["context"]
        i = user_msg["index"]

        # Check for corrections (HIGH)
        for pattern in CORRECTION_PATTERNS:
            if match := re.search(pattern, content):
                signals.append(
                    {
                        "confidence": "HIGH",
                        "confidence_score": 0.85,
                        "type": "correction",
                        "content": content,
                        "context": context,
                        "skills": skills_used if skills_used else ["general"],
                        "match": match.groups() if match.groups() else (content,),
                        "description": extract_correction_description(content, match),
                        "detection_method": "regex",
                    }
                )

        # Check for approvals (MEDIUM)
        prev_msg = messages[i - 1] if i > 0 else None
        if prev_msg and prev_msg.get("role") == "assistant":
            for pattern in APPROVAL_PATTERNS:
                if re.search(pattern, content):
                    signals.append(
                        {
                            "confidence": "MEDIUM",
                            "confidence_score": 0.65,
                            "type": "approval",
                            "content": content,
                            "context": context,
                            "skills": skills_used if skills_used else ["general"],
                            "previous_approach": extract_approach(prev_msg),
                            "description": "Approved approach",
                            "detection_method": "regex",
                        }
                    )

        # Check for questions (LOW)
        for pattern in QUESTION_PATTERNS:
            if match := re.search(pattern, content):
                signals.append(
                    {
                        "confidence": "LOW",
                        "confidence_score": 0.45,
                        "type": "question",
                        "content": content,
                        "context": context,
                        "skills": skills_used if skills_used else ["general"],
                        "suggestion": match.group(1) if match.groups() else content,
                        "description": f"Consider: {match.group(1) if match.groups() else content}",
                        "detection_method": "regex",
                    }
                )

    # Phase 2: Semantic analysis (if enabled)
    if use_semantic:
        if not SEMANTIC_AVAILABLE:
            print("Warning: Semantic detector not available. Using regex only.")
        else:
            print("Running semantic analysis...")
            signals = enhance_with_semantic(
                signals, user_messages, skills_used, model=semantic_model
            )

    # Phase 3: Tool error extraction
    if include_tool_errors and TOOL_ERROR_AVAILABLE and transcript_path:
        try:
            from pathlib import Path as PathlibPath

            tool_errors = extract_tool_errors(PathlibPath(transcript_path))
            if tool_errors:
                aggregated = aggregate_errors(tool_errors, min_occurrences=2)
                for agg_error in aggregated:
                    signals.append(
                        {
                            "confidence": "HIGH" if agg_error["confidence"] >= 0.85 else "MEDIUM",
                            "confidence_score": agg_error["confidence"],
                            "type": "tool_error",
                            "content": f"Technical error: {agg_error['error_type']}",
                            "context": agg_error["sample_errors"][:2],  # First 2 samples
                            "skills": ["general"],
                            "error_type": agg_error["error_type"],
                            "count": agg_error["count"],
                            "suggested_guideline": agg_error["suggested_guideline"],
                            "description": f"Repeated {agg_error['error_type']} error ({agg_error['count']} occurrences)",
                            "detection_method": "tool_error_extraction",
                        }
                    )
                    print(f"  -> Tool error: {agg_error['error_type']} ({agg_error['count']}x)")
        except Exception as e:
            print(f"Warning: Tool error extraction failed: {e}")

    return group_by_skill(signals)


def enhance_with_semantic(
    regex_signals: list[dict[str, Any]],
    user_messages: list[dict[str, Any]],
    skills_used: list[str],
    model: str | None = None,
) -> list[dict[str, Any]]:
    """
    Enhance regex signals with semantic validation.
    Uses semantic_validator to filter false positives from HIGH/MEDIUM confidence signals.
    Also finds signals that regex missed.
    """
    enhanced_signals = []

    # Validate HIGH/MEDIUM regex signals using semantic_validator
    if VALIDATOR_AVAILABLE:
        for signal in regex_signals:
            confidence_score = signal.get("confidence_score", 0.0)

            # Only validate HIGH and MEDIUM confidence signals
            if confidence_score >= 0.5:  # MEDIUM threshold
                validation_result = validate_signal(signal, model=model)

                if validation_result["status"] == "validated":
                    # Signal passed semantic validation
                    merged = {**signal}
                    merged["semantic_confidence"] = validation_result["semantic_confidence"]
                    merged["semantic_reasoning"] = validation_result["reason"]
                    merged["extracted_learning"] = validation_result["extracted_learning"]
                    merged["detection_method"] = "regex+semantic_validated"
                    enhanced_signals.append(merged)
                elif validation_result["status"] == "rejected":
                    # Signal failed semantic validation (false positive)
                    # Skip this signal - don't add to enhanced_signals
                    continue
                else:
                    # Error during validation - keep original signal
                    enhanced_signals.append(signal)
            else:
                # LOW confidence signals - skip validation, keep as-is
                enhanced_signals.append(signal)
    else:
        # Fallback: keep all regex signals if validator not available
        enhanced_signals = list(regex_signals)

    # Also find signals that regex missed (using semantic detector)
    if SEMANTIC_AVAILABLE:
        for user_msg in user_messages:
            content = user_msg["content"]
            context = user_msg["context"]

            # Run semantic analysis
            result = semantic_analyze(content, model=model)

            if result is None:
                continue

            if not result.get("is_learning"):
                continue

            # Check if regex already found this
            already_found = False
            for sig in regex_signals:
                if sig["content"] == content:
                    already_found = True
                    break

            if already_found:
                continue

            # New signal found by semantic only
            conf = result.get("confidence", 0.5)
            enhanced_signals.append(
                {
                    "confidence": "HIGH" if conf >= 0.8 else "MEDIUM" if conf >= 0.6 else "LOW",
                    "confidence_score": conf,
                    "type": result.get("type", "correction"),
                    "content": content,
                    "context": context,
                    "skills": skills_used if skills_used else ["general"],
                    "description": result.get("extracted_learning", "Learning detected"),
                    "extracted_learning": result.get("extracted_learning"),
                    "semantic_reasoning": result.get("reasoning"),
                    "detection_method": "semantic",
                }
            )

    return enhanced_signals


def find_latest_transcript() -> str | None:
    """Find the most recent transcript file"""
    try:
        if os.getenv("TRANSCRIPT_PATH"):
            return os.getenv("TRANSCRIPT_PATH")

        session_dir = Path(
            os.getenv("SESSION_DIR", Path.home() / ".claude" / "session-env")
        ).expanduser()
        if session_dir.exists():
            transcripts = list(session_dir.glob("*/transcript.jsonl"))
            if transcripts:
                return str(max(transcripts, key=lambda p: p.stat().st_mtime))
    except Exception as e:
        print(f"Error finding transcript: {e}")

    return None


def load_transcript(path: str) -> list[dict[str, Any]]:
    """Load JSONL transcript into message list"""
    messages = []
    try:
        with open(path) as f:
            for line in f:
                if line.strip():
                    try:
                        msg = json.loads(line)
                        messages.append(msg)
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"Error loading transcript: {e}")

    return messages


def find_skill_invocations(messages: list[dict[str, Any]]) -> list[str]:
    """Find which skills were invoked in conversation"""
    skills = set()
    for msg in messages:
        if "tool_uses" in msg:
            for tool in msg.get("tool_uses", []):
                if tool.get("name") == "Skill":
                    params = tool.get("parameters", {})
                    if "skill" in params:
                        skills.add(params["skill"])

        content = str(msg.get("content", ""))
        if matches := re.findall(r"/([a-z][a-z0-9-]*)", content):
            skills.update(matches)

    return list(skills)


def extract_approach(message: dict[str, Any]) -> str:
    """Extract the approach Claude took from assistant message"""
    content = str(message.get("content", ""))
    return content[:500]


def extract_correction_description(content: str, match) -> str:
    """Extract a human-readable description from correction pattern"""
    if match.groups():
        if len(match.groups()) == 2:
            return f"Use '{match.group(2)}' instead of '{match.group(1)}'"
        elif len(match.groups()) == 1:
            return f"Correction: {match.group(1)}"
    return "User provided correction"


def group_by_skill(signals: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group signals by the skills they relate to"""
    grouped = {}
    for signal in signals:
        for skill in signal.get("skills", ["general"]):
            if skill not in grouped:
                grouped[skill] = []
            grouped[skill].append(signal)
    return grouped


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract learning signals from Claude Code transcripts"
    )
    parser.add_argument(
        "transcript", nargs="?", help="Path to transcript file (auto-detected if not provided)"
    )
    parser.add_argument(
        "--semantic",
        action="store_true",
        help="Use AI-powered semantic analysis (slower but more accurate, multi-language)",
    )
    parser.add_argument(
        "--model", default=None, help="Model for semantic analysis (default: haiku)"
    )
    parser.add_argument(
        "--no-tool-errors", action="store_true", help="Disable tool error extraction"
    )

    args = parser.parse_args()

    if args.semantic and not SEMANTIC_AVAILABLE:
        print("Error: semantic_detector.py not found in same directory")
        print("Make sure semantic_detector.py is in reflect/scripts/")
        exit(1)

    signals = extract_signals(
        args.transcript,
        use_semantic=args.semantic,
        semantic_model=args.model,
        include_tool_errors=not args.no_tool_errors,
    )

    print(json.dumps(signals, indent=2, ensure_ascii=False))
