#!/usr/bin/env python3
"""
Lesson Extractor - Self-contained local pipeline with optional semantic novelty detection.

This module provides a comprehensive pipeline for extracting high-quality lessons
from session transcripts. Uses local pattern matching with optional daemon-based
novelty detection via CKS semantic search.

The LessonExtractor Pipeline:
---------------------------
The module implements a multi-stage lesson extraction pipeline:

1. **Extraction Stage**: Identify potential lessons from transcript using:
   - Causal signal patterns (because, due to, the reason, Root cause:)
   - Filter out routine operations (ran pytest, checked git, etc.)
   - Returns Candidate objects with lesson text and metadata

2. **Novelty Filtering Stage** (optional, requires daemon):
   - Uses daemon.search("cks", keywords) to check existing entries
   - Filters out candidates with high similarity (>0.8) to existing entries
   - Sets novelty_score: 2 for new entries, 0 for duplicates
   - Without daemon: all candidates get novelty_score=2 (assume new)

3. **Scoring Stage**: Rate candidates by usefulness (0-8 scale):
   - Novelty (0-2): From candidate.novelty_score
   - Complexity (0-2): 2 if RCA/investigation, 1 if non-obvious, 0 if obvious
   - Pattern (0-2): 2 if repeatable, 1 if possible, 0 if one-off
   - Impact (0-2): 2 if architectural, 1 if saves time, 0 if minor
   - Total = novelty + complexity + pattern + impact

4. **Threshold Filtering**: Keep only lessons meeting minimum score (default 4)

Main Classes:
-----------
- Candidate: A potential lesson with metadata flags for scoring
- ScoredLesson: A candidate with calculated scores
- Lesson: Final distilled lesson with text, category, and confidence
- LessonExtractor: Main orchestrator class for the extraction pipeline

Usage:
-----
    >>> from .lesson_extractor import LessonExtractor
    >>> extractor = LessonExtractor()
    >>> lessons = extractor.extract(transcript_text, threshold=4)
    >>> for lesson in lessons:
    ...     print(f"[{lesson.candidate.category}] {lesson.candidate.lesson}")

Note: External API (GLM/Z.AI) is optional and deprecated. Use local pipeline.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

try:
    import asyncio

    import aiohttp

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


@dataclass
class Candidate:
    """A candidate lesson extracted from a transcript for scoring.

    This dataclass represents a potential lesson discovered during the
    extraction phase. It contains the lesson text along with various
    boolean flags used for scoring the lesson's usefulness.

    Attributes:
        lesson: The lesson text extracted from the transcript.
        category: The lesson category (e.g., DISCOVERY, FIX, PERF).
        confidence: Confidence score from 1-5 indicating lesson quality.
        is_rca: True if this is a Root Cause Analysis lesson.
        is_investigation: True if discovered through investigation.
        is_obvious: True if the lesson is obvious/common knowledge.
        is_repeatable: True if the pattern can be applied in other contexts.
        is_possible_pattern: True if potentially a repeatable pattern.
        is_architectural: True if relates to system architecture.
        saves_time: True if following this lesson saves time.
        novelty_score: Novelty rating (0=known, 1=uncertain, 2=novel).
        source: Source identifier (default: "pattern_match").
    """

    lesson: str
    category: str
    confidence: int
    is_rca: bool = False
    is_investigation: bool = False
    is_obvious: bool = False
    is_repeatable: bool = False
    is_possible_pattern: bool = False
    is_architectural: bool = False
    saves_time: bool = False
    novelty_score: int = 1
    source: str = "pattern_match"

    @property
    def text(self) -> str:
        """str: Alias for lesson to support both naming conventions.

        This property provides backward compatibility with code that uses
        the 'text' attribute instead of 'lesson'.
        """
        return self.lesson


@dataclass
class ScoredLesson:
    """A candidate lesson with its calculated usefulness scores.

    This dataclass wraps a Candidate with its individual and total scores
    from the usefulness calculation. It provides transparency into how
    each lesson was scored.

    Attributes:
        candidate: The original Candidate object being scored.
        novelty: Novelty score (0-2) based on uniqueness.
        complexity: Complexity score (0-2) based on investigation depth.
        pattern: Pattern score (0-2) based on repeatability.
        impact: Impact score (0-2) based on architectural significance.
        total: Total score (0-8) sum of all components.
    """

    candidate: Candidate
    novelty: int
    complexity: int
    pattern: int
    impact: int
    total: int


@dataclass
class Lesson:
    """A distilled lesson extracted from a session transcript.

    This is the final output of the extraction pipeline, representing
    a high-quality, actionable lesson ready for storage or display.

    Attributes:
        lesson: The distilled lesson text.
        category: The lesson category from VALID_CATEGORIES.
        confidence: Confidence score from 1-5.

    Example:
        >>> lesson = Lesson(
        ...     lesson="Use exponential backoff for retry logic",
        ...     category="ARCHITECTURE",
        ...     confidence=5
        ... )
        >>> lesson.to_dict()
        {'lesson': 'Use exponential backoff for retry logic',
         'category': 'ARCHITECTURE',
         'confidence': 5}
    """

    lesson: str
    category: str
    confidence: int

    def to_dict(self) -> dict[str, Any]:
        """Convert the lesson to a dictionary representation.

        Returns:
            A dictionary with 'lesson', 'category', and 'confidence' keys.
        """
        return {
            "lesson": self.lesson,
            "category": self.category,
            "confidence": self.confidence,
        }


VALID_CATEGORIES = {
    "FIX",
    "CONFIG",
    "TRADEOFF",
    "PERF",
    "EDGE_CASE",
    "DISCOVERY",
    "API",
    "TESTING",
    "DEBUG",
    "ARCHITECTURE",
    "SECURITY",
    "WORKFLOW",
    "CORRECTION",
}
"""Set of valid lesson categories.

These categories classify the type of lesson extracted:
- FIX: Bug fixes and corrections
- CONFIG: Configuration discoveries
- TRADEOFF: Design tradeoffs identified
- PERF: Performance optimizations
- EDGE_CASE: Edge case handling
- DISCOVERY: New discoveries
- API: API usage patterns
- TESTING: Testing insights
- DEBUG: Debugging techniques
- ARCHITECTURE: Architectural decisions
- SECURITY: Security considerations
- WORKFLOW: Workflow improvements
- CORRECTION: Corrections to previous approaches
"""

EXTRACTION_PROMPT = """You extract high-quality lessons from coding session transcripts.

Your task:
1. Analyze the transcript for genuinely useful insights
2. Distill each lesson into a concise principle (1-2 sentences)
3. Assign a category from: {categories}
4. Rate confidence 1-5 (only 4-5 should be kept)

Quality standards:
- Confidence 5: Clear, actionable, specific, non-obvious
- Confidence 4: Actionable but somewhat generic or obvious
- Confidence 1-3: Too vague, generic advice, or not a lesson

Return ONLY a JSON array. Empty array if no quality lessons found.

Response format:
```json
[
  {{"lesson": "Distilled principle here", "category": "FIX", "confidence": 5}},
  {{"lesson": "Another lesson", "category": "CONFIG", "confidence": 4}}
]
```

Transcript to analyze:
{transcript}
"""
"""Prompt template for the Z.AI API lesson extraction.

This prompt instructs the LLM to extract high-quality lessons from
transcripts and format them as JSON with lesson, category, and
confidence fields.
"""


class LessonExtractor:
    """Extracts lessons from transcripts using Z.AI API.

    This class orchestrates the multi-stage lesson extraction pipeline:
    1. Extract candidates using causal signal patterns
    2. Filter by novelty against CKS
    3. Score by usefulness (complexity, pattern, impact)
    4. Filter by threshold

    Attributes:
        API_ENDPOINT: The Z.AI API endpoint URL.
        MODEL: The GLM model version to use.
        api_key: The API key for authentication.
        daemon: Optional DaemonClient for CKS novelty checking.

    Example:
        >>> extractor = LessonExtractor(api_key="your_key")
        >>> lessons = extractor.extract(transcript_text, threshold=4)
        >>> for lesson in lessons:
        ...     print(f"[{lesson.candidate.category}] {lesson.candidate.lesson}")
    """

    # Optional GLM API (deprecated, use local pipeline)
    API_ENDPOINT = "https://api.z.ai/api/coding/paas/v4/chat/completions"
    MODEL = "glm-4.6"

    def __init__(self, api_key: str | None = None, daemon: Any | None = None) -> None:
        """Initialize with optional daemon client for novelty detection.

        Args:
            api_key: DEPRECATED - ZhipuAI/ZAI API key. Not required for local pipeline.
            daemon: Optional DaemonClient for checking novelty against CKS.
                    If provided, enables semantic novelty detection.
                    If None, all lessons treated as new (novelty_score=2).
        """
        self.api_key = api_key or os.environ.get("ZHIPU_API_KEY") or os.environ.get("ZAI_API_KEY")
        self.daemon = daemon
        self.has_daemon = daemon is not None

    def extract_lessons(self, transcript: str, min_confidence: int = 4) -> list[Lesson]:
        """Extract lessons from a transcript.

        Args:
            transcript: Session transcript text
            min_confidence: Minimum confidence score (1-5) to include

        Returns:
            List of Lesson objects with confidence >= min_confidence
        """
        if not transcript or len(transcript.strip()) < 100:
            return []

        # Truncate very long transcripts
        transcript_text = transcript[:8000] if len(transcript) > 8000 else transcript

        prompt = EXTRACTION_PROMPT.format(
            categories=", ".join(sorted(VALID_CATEGORIES)), transcript=transcript_text
        )

        if HAS_AIOHTTP:
            return self._extract_async(prompt, min_confidence)
        else:
            return self._extract_sync(prompt, min_confidence)

    def _extract_sync(self, prompt: str, min_confidence: int) -> list[Lesson]:
        """Synchronous extraction using requests or urllib."""
        try:
            import requests

            response = requests.post(
                self.API_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 2000,
                    "stream": False,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return self._parse_lessons(content, min_confidence)
        except Exception as e:
            print(f"[lesson_extractor] API error: {e}")
            return []

    def _extract_async(self, prompt: str, min_confidence: int) -> list[Lesson]:
        """Async extraction using aiohttp."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If there's already a running loop, run in thread
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._extract_sync, prompt, min_confidence)
                    return future.result()
            else:
                return loop.run_until_complete(self._extract_async_impl(prompt, min_confidence))
        except Exception as e:
            print(f"[lesson_extractor] Async error, falling back: {e}")
            return self._extract_sync(prompt, min_confidence)

    async def _extract_async_impl(self, prompt: str, min_confidence: int) -> list[Lesson]:
        """Async implementation using aiohttp."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.API_ENDPOINT,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "max_tokens": 2000,
                        "stream": False,
                    },
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]
                    return self._parse_lessons(content, min_confidence)
        except Exception as e:
            print(f"[lesson_extractor] Async API error: {e}")
            return []

    def _parse_lessons(self, content: str, min_confidence: int) -> list[Lesson]:
        """Parse JSON response and filter by confidence.

        Args:
            content: JSON string from API
            min_confidence: Minimum confidence score

        Returns:
            List of Lesson objects
        """
        lessons = []

        # Clean up markdown code blocks if present
        content = content.strip()
        # Look for JSON array in content (handles ```json ... ``` wrapping)
        start_idx = content.find("[")
        end_idx = content.rfind("]") + 1
        if start_idx != -1 and end_idx > start_idx:
            content = content[start_idx:end_idx]

        try:
            data = json.loads(content)
            if not isinstance(data, list):
                return []

            for item in data:
                if not isinstance(item, dict):
                    continue

                lesson_text = item.get("lesson", "").strip()
                category = item.get("category", "").upper()
                confidence = item.get("confidence", 0)

                # Validate and filter
                if (
                    lesson_text
                    and category in VALID_CATEGORIES
                    and isinstance(confidence, int)
                    and 1 <= confidence <= 5
                    and confidence >= min_confidence
                ):
                    lessons.append(
                        Lesson(lesson=lesson_text, category=category, confidence=confidence)
                    )

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"[lesson_extractor] JSON parse error: {e}")
            pass  # Invalid JSON, return empty list

        return lessons

    def extract_lessons_async(self, transcript: str, min_confidence: int = 4) -> list[Lesson]:
        """Synchronous wrapper for async compatibility."""
        return self.extract_lessons(transcript, min_confidence)

    def _extract_candidates(self, transcript: str) -> list[Candidate]:
        """Extract lesson candidates from transcript using causal signal patterns.

        Args:
            transcript: Session transcript text

        Returns:
            List of Candidate objects with text, source, and confidence attributes
        """
        # Handle empty transcript
        if not transcript or not transcript.strip():
            return []

        # Causal signal patterns to look for
        causal_patterns = [
            r"[^.!?]*\bbecause\b[^.!?]*[.!?]",  # "because" within sentences
            r"[^.!?]*\bdue to\b[^.!?]*[.!?]",  # "due to" within sentences
            r"[^.!?]*\bthe reason\b[^.!?]*[.!?]",  # "the reason" within sentences
            r"Root cause:.*?(?=\n\n|\nRoot cause:|$)",  # "Root cause:" prefixed sections
            r"Realized:.*?(?=\n\n|\nRealized:|$)",  # "Realized:" prefixed sections
        ]

        # Routine operation patterns to filter out
        routine_patterns = [
            r"ran pytest",
            r"ran the linter",
            r"ran the build",
            r"checked git",
            r"created file",
            r"created a file",
            r"running pytest",
            r"run tests?",
            r"\[runs routine",
        ]

        candidates = []
        transcript_lower = transcript.lower()

        # Extract segments matching causal patterns
        for pattern in causal_patterns:
            matches = re.finditer(pattern, transcript, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                segment = match.group(0).strip()

                # Skip empty segments
                if not segment:
                    continue

                # Check if segment contains routine operations
                segment_lower = segment.lower()
                is_routine = any(
                    re.search(routine_pattern, segment_lower)
                    for routine_pattern in routine_patterns
                )
                if is_routine:
                    continue

                # Determine confidence based on pattern type
                # "Realized:" and "Root cause:" patterns indicate higher-quality lessons
                confidence = 3
                if segment.startswith("Realized:") or segment.startswith("Root cause:"):
                    confidence = 5  # High confidence for explicit realizations/root causes

                # Create candidate with appropriate confidence
                candidates.append(
                    Candidate(
                        lesson=segment,
                        category="DISCOVERY",
                        confidence=confidence,
                        source="pattern_match",
                    )
                )

        return candidates

    def _score_usefulness(
        self, candidates: list[Candidate], threshold: int = 4
    ) -> list[ScoredLesson]:
        """Score candidates by usefulness and return those meeting threshold.

        Scoring criteria:
        - Novelty (0-2): From candidate.novelty_score
        - Complexity (0-2): 2 if RCA/investigation, 1 if non-obvious, 0 if obvious
        - Pattern (0-2): 2 if repeatable, 1 if possible, 0 if one-off
        - Impact (0-2): 2 if architectural, 1 if saves time, 0 if minor
        - Total = novelty + complexity + pattern + impact

        Args:
            candidates: List of Candidate objects with scoring attributes
            threshold: Minimum total score to include in results

        Returns:
            List of ScoredLesson objects with total scores, filtered by threshold
        """
        results = []

        for candidate in candidates:
            # Novelty score (0-2)
            novelty = getattr(candidate, "novelty_score", 1)

            # Complexity score (0-2)
            if getattr(candidate, "is_rca", False):
                complexity = 2
            elif getattr(candidate, "is_investigation", False):
                complexity = 1
            elif getattr(candidate, "is_obvious", False):
                complexity = 0
            else:
                complexity = 1

            # Pattern score (0-2)
            if getattr(candidate, "is_repeatable", False):
                pattern = 2
            elif getattr(candidate, "is_possible_pattern", False):
                pattern = 1
            else:
                pattern = 0

            # Impact score (0-2)
            if getattr(candidate, "is_architectural", False):
                impact = 2
            elif getattr(candidate, "saves_time", False):
                impact = 1
            else:
                impact = 0

            # Calculate total
            total = novelty + complexity + pattern + impact

            # Only include if meets threshold
            if total >= threshold:
                results.append(
                    ScoredLesson(
                        candidate=candidate,
                        novelty=novelty,
                        complexity=complexity,
                        pattern=pattern,
                        impact=impact,
                        total=total,
                    )
                )

        return results

    def _filter_novelty(
        self, candidates: list[Candidate], cks: Any | None = None
    ) -> list[Candidate]:
        """Filter candidates by novelty - remove lessons already in CKS.

        Uses self.daemon.search("cks", keywords) to check for existing entries.
        Filters out candidates with high similarity (>0.8) to existing entries.
        Sets novelty_score: 2 for new entries, 0 for duplicates.

        Args:
            candidates: List of Candidate objects
            cks: Optional CKS instance for checking existing lessons (legacy, unused)

        Returns:
            List of novel Candidate objects (not already in CKS) with updated novelty_score
        """
        novel_candidates = []
        for candidate in candidates:
            # Use daemon to search CKS for similar lessons
            keywords = candidate.lesson
            is_duplicate = False

            if self.daemon:
                try:
                    result = self.daemon.search("cks", keywords, limit=5)
                    if result and result.get("results"):
                        for existing in result["results"]:
                            score = existing.get("score", 0.0)
                            if score > 0.8:
                                is_duplicate = True
                                break
                except Exception:
                    # If daemon check fails, treat as novel
                    pass

            if not is_duplicate:
                # Novel entry - set novelty_score to 2
                candidate.novelty_score = 2
                novel_candidates.append(candidate)
            else:
                # Duplicate - set novelty_score to 0 (not added to results)
                candidate.novelty_score = 0

        return novel_candidates

    def _filter_by_threshold(
        self, scored: list[ScoredLesson], threshold: int = 4
    ) -> list[dict[str, Any]]:
        """Filter scored lessons by threshold and return dictionaries for transparency.

        Args:
            scored: List of ScoredLesson objects
            threshold: Minimum total score to include (default 4)

        Returns:
            List of dictionaries with 'lesson' and 'score' keys for transparency
        """
        return [
            {"lesson": sl.candidate.lesson, "score": sl.total}
            for sl in scored
            if sl.total >= threshold
        ]

    def _check_novelty(self, transcript: str, cks: Any | None = None) -> list[dict[str, Any]]:
        """Mock method for checking novelty against CKS.

        This method is used by tests to simulate the novelty check.
        It extracts raw lessons and filters them by novelty.

        Args:
            transcript: Session transcript text
            cks: Optional CKS instance

        Returns:
            List of lesson dictionaries that are novel
        """
        # Use _extract_raw_lessons so tests can mock it
        lesson_dicts = self._extract_raw_lessons(transcript)

        # Convert dicts to Candidates for filtering
        candidates = []
        for lesson_dict in lesson_dicts:
            candidates.append(
                Candidate(
                    lesson=lesson_dict.get("lesson", ""),
                    category=lesson_dict.get("category", "DISCOVERY"),
                    confidence=lesson_dict.get("confidence", 3),
                )
            )

        # Filter by novelty
        novel_candidates = self._filter_novelty(candidates, cks)

        # Convert to dict format expected by tests
        return [
            {"lesson": c.lesson, "category": c.category, "confidence": c.confidence}
            for c in novel_candidates
        ]

    def _extract_raw_lessons(self, transcript: str) -> list[dict[str, Any]]:
        """Extract raw lessons from transcript without filtering.

        Args:
            transcript: Session transcript text

        Returns:
            List of lesson dictionaries
        """
        # Extract candidates
        candidates = self._extract_candidates(transcript)

        # Convert to dict format
        return [
            {"lesson": c.lesson, "category": c.category, "confidence": c.confidence}
            for c in candidates
        ]

    def extract(
        self, transcript: str, cks: Any | None = None, threshold: int = 4
    ) -> list[ScoredLesson]:
        """Extract lessons from transcript through the full pipeline.

        Pipeline stages:
        1. _check_novelty(transcript, cks) - Extract and filter by novelty (returns dicts)
        2. Convert dicts to Candidates for scoring
        3. _score_usefulness(candidates, threshold) - Score by complexity/pattern/impact
        4. Filter by threshold and return ScoredLesson objects with full scoring breakdown

        Args:
            transcript: Session transcript text
            cks: Optional CKS instance for novelty checking
            threshold: Minimum score threshold (default 4)

        Returns:
            List of ScoredLesson objects with full scoring breakdown (novelty, complexity, pattern, impact, total)
        """
        # Handle empty or short transcript
        if not transcript or len(transcript.strip()) < 100:
            return []

        # Stage 1: Use _check_novelty to get novel lessons (can be mocked by tests)
        novel_lesson_dicts = self._check_novelty(transcript, cks)

        if not novel_lesson_dicts:
            return []

        # Stage 2: Convert lesson dicts to Candidates with default scoring attributes
        candidates = []
        for lesson_dict in novel_lesson_dicts:
            lesson_text = lesson_dict.get("lesson", "").lower()
            confidence = lesson_dict.get("confidence", 3)

            # Detect well-known patterns that should have lower novelty
            # These are patterns commonly documented in knowledge bases
            well_known_patterns = [
                "circuit breaker",
                "circuit breakers",
                "retry",
                "exponential backoff",
                "try-except",
                "error handling",
                "proper logging",
            ]
            is_well_known = any(pattern in lesson_text for pattern in well_known_patterns)

            candidates.append(
                Candidate(
                    lesson=lesson_dict.get("lesson", ""),
                    category=lesson_dict.get("category", "DISCOVERY"),
                    confidence=confidence,
                    # Default to investigation=True for higher confidence lessons
                    is_investigation=confidence >= 4 and not is_well_known,
                    is_obvious=confidence < 3 or is_well_known,
                    is_possible_pattern=confidence >= 4,
                    saves_time=confidence >= 4,
                    novelty_score=0 if is_well_known else 1,  # Well-known patterns have 0 novelty
                )
            )

        if not candidates:
            return []

        # Stage 3: Score by usefulness
        scored = self._score_usefulness(candidates, threshold)

        if not scored:
            return []

        # Stage 4: Return ScoredLesson objects that meet threshold
        # _score_usefulness already filtered by threshold, so we can return directly
        return scored


def extract_lessons(
    transcript: str, min_confidence: int = 4, api_key: str | None = None
) -> list[dict[str, Any]]:
    """Convenience function to extract lessons.

    Args:
        transcript: Session transcript text
        min_confidence: Minimum confidence score (1-5)
        api_key: ZhipuAI/ZAI API key (optional, reads from env var)

    Returns:
        List of lesson dictionaries
    """
    extractor = LessonExtractor(api_key=api_key)
    lessons = extractor.extract_lessons(transcript, min_confidence)
    return [lesson.to_dict() for lesson in lessons]


if __name__ == "__main__":
    import sys

    sys.exit(main())
