"""SuspicionDetector - Surface suspicious conversational patterns autonomously.

Priority: P1 (runs during gap detection)
Purpose: Detect conversation-level signals that suggest hidden problems,
misalignment, or unaddressed concerns — WITHOUT relying on user feedback.

What it detects:
- Contradictions: claims X was done but evidence suggests otherwise
- Confusion gaps: expressed confusion that wasn't resolved
- Resigned acceptance: silent agreement after raised concerns
- Commitment reversal: "I take it back", "wait no", "actually"
- Misalignment signals: user re-explaining something the agent should know

What it is NOT:
- NOT a replacement for user-reported issues
- NOT a psychological analysis tool — purely pattern-based
- NOT infallible — these are suspicion signals, not proof of problems

The key distinction from SessionOutcomeDetector:
- SessionOutcomeDetector: what was STATED but not done
- SuspicionDetector: what was HIDDEN or CONTRADICTED

This is the "trust but verify" layer — surfacing things that seem off
even when the user hasn't explicitly labeled them as problems.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass
class SuspicionItem:
    """A single suspicion signal found in conversation."""

    category: Literal[
        "contradiction",
        "unresolved_confusion",
        "resigned_acceptance",
        "commitment_reversal",
        "misalignment",
        "confidence_mirage",
        "silent_failure_masking",
        "excessive_breadcrumbs",
        "reasoning_action",
    ]
    content: str
    turn_number: int
    confidence: float  # 0.0 to 1.0
    source_message: str = ""  # The full message containing the signal
    prior_context: str = ""  # What was said before that this contradicts


@dataclass
class SuspicionResult:
    """Result of suspicion detection."""

    items: list[SuspicionItem]
    total_count: int

    def to_gaps(self) -> list[dict]:
        """Convert items to GTO gap format for RSN integration."""
        gaps = []
        for idx, item in enumerate(self.items):
            gap_id = f"SUSPIC-{item.category[:4].upper()}-{idx + 1:03d}"

            severity_map = {
                "contradiction": "high",
                "commitment_reversal": "high",
                "unresolved_confusion": "medium",
                "resigned_acceptance": "medium",
                "misalignment": "medium",
                "confidence_mirage": "high",
                "silent_failure_masking": "high",
                "excessive_breadcrumbs": "low",
                "reasoning_action": "high",
            }
            category_display = {
                "contradiction": "Contradiction Detected",
                "commitment_reversal": "Commitment Reversal",
                "unresolved_confusion": "Unresolved Confusion",
                "resigned_acceptance": "Resigned Acceptance",
                "misalignment": "Conversational Misalignment",
                "confidence_mirage": "Confidence Mirage",
                "silent_failure_masking": "Silent Failure Masking",
                "excessive_breadcrumbs": "Excessive Breadcrumbs",
                "reasoning_action": "Reasoning-Action Mismatch",
            }
            gaps.append(
                {
                    "id": gap_id,
                    "type": f"suspicion_{item.category}",
                    "severity": severity_map.get(item.category, "medium"),
                    "message": f"[{category_display.get(item.category, item.category)}] {item.content}",
                    "file_path": None,
                    "line_number": None,
                    "confidence": item.confidence,
                    "effort_estimate_minutes": 15,
                    "theme": "suspicion_signals",
                    "metadata": {
                        "category": item.category,
                        "source_message": item.source_message[:200]
                        if item.source_message
                        else None,
                        "prior_context": item.prior_context[:200] if item.prior_context else None,
                    },
                }
            )
        return gaps


class SuspicionDetector:
    """
    Detect suspicious conversational patterns autonomously.

    Does NOT require user to label something as suspicious.
    Instead, it identifies patterns that humans find concerning:
    - Contradictions between statements
    - Unresolved confusion
    - Acceptance despite raised concerns
    - Reversals of prior commitments
    """

    # === CONTRADICTION PATTERNS ===
    # User claims X was done/decided, but this conflicts with conversation flow
    CONTRADICTION_PATTERNS = [
        # "but I thought X was done/decided"
        (
            r"but I thought (?:we|i|it) (?:already )?(?:did|decided|finished)(?: it)? (.{10,120})",
            0.8,
        ),
        # "X was supposed to happen"
        (r"(?:X|it) (?:was supposed to|should've|was meant to) (.{10,120})", 0.75),
        # "but we agreed on X" when X wasn't agreed
        (r"but we (?:agreed|decided) (?:on |that )?([^\.]{10,60})", 0.7),
        # "I thought we were going to" when clearly not
        (r"I thought we were going to ([^\.]{10,60})", 0.65),
    ]

    # === COMMITMENT REVERSAL PATTERNS ===
    # User explicitly takes something back
    REVERSAL_PATTERNS = [
        (r"(?:wait|no|oh) [,.\-]? (?:actually|no[,.\-]?|take that back|i take it back)", 0.9),
        (r"actually [,.\-]?(?:on second thought|i take it back|let me reconsider)", 0.9),
        (r"(?:no |wait )[,.\-]?(?:that's wrong|i was wrong|i'm wrong)", 0.85),
        (r"(?:I take it back|i'm taking that back|i take that back)", 0.9),
        (r"(?:nevermind|never mind) [,.\-]?(?:that|what I said)", 0.7),
        (r"forget (?:what I said|that|i said)", 0.7),
        (r"(?:on second thought|second thought) [,.\-]?(.{10,50})", 0.75),
    ]

    # === CONFUSION PATTERNS ===
    # User expresses confusion or lack of understanding
    CONFUSION_PATTERNS = [
        (r"(?:I'm|I am) (?:confused|not following|lost)", 0.85),
        (r"(?:I'm|I am) (?:still )?confused about (.{10,120})", 0.85),
        (r"this doesn't (?:make sense|add up)", 0.8),
        (r"what (?:do you mean|do you mean by)", 0.75),
        (r"(?:I )?don't (?:understand|get|follow) (.{10,120})", 0.75),
        (r"(?:I'm|I am) (?:still )?unclear on (.{10,120})", 0.8),
        (r"(?:I|we) (?:might be|maybe) (?:missing|misunderstanding) (.{10,50})", 0.7),
        (r"(?:wait|Wait) [,.\-]?(?:what|why|how|who)", 0.65),
        (r"that (?:doesn't|does not) seem right", 0.7),
        (r"something (?:seems off|isn't adding up|doesn't add up)", 0.75),
    ]

    # === RESIGNED ACCEPTANCE PATTERNS ===
    # User accepts something despite having expressed concerns
    # These are caught by checking: prior turn had concern, this turn accepts
    RESIGNED_PATTERNS = [
        (
            r"(?:fine|okay|ok|alright|yeah) [,.\-]?(?:I guess|i suppose|fine by me|i'll allow it)",
            0.6,
        ),
        (r"(?:I|just) (?:suppose|guess) (?:that's|it's) (?:fine|okay|acceptable)", 0.6),
        (r"(?:whatever|whatev) [,.\-]?(?:you|it) (?:say|think|want)", 0.5),
        (r"(?:I )?(?:can't argue with that|there's no arguing with that)", 0.55),
    ]

    # === MISALIGNMENT PATTERNS ===
    # User re-explains something the agent should have known/handled
    MISALIGNMENT_PATTERNS = [
        # Re-explaining after agent did something unexpected
        (r"(?:I|I've) already (?:told you|told|explained) (?:you|that|this) (.{10,120})", 0.8),
        (r"(?:as I said|like I said|I said) (?:before |already )?(.{10,120})", 0.75),
        # User restating requirements after agent deviation
        (
            r"(?:the |my )?(?:requirement|request|goal) (?:was|is|was to) (?:still |just )?(.{10,120})",
            0.7,
        ),
        # "we need to" after something was supposed to be done
        (r"we (?:still |just |really )?need to (.{10,120})", 0.6),
        # Agent missed something obvious
        (
            r"(?:you|yours?) (?:(?:seem to|appears to) have |have )?(?:missed|forgotten|overlooked) (.{10,120})",
            0.75,
        ),
    ]

    # Completion signals that, when present, reduce suspicion severity
    COMPLETION_SIGNALS = [
        r"(?:done|finished|completed|implemented|fixed|added|created|solved|resolved)",
        r"(?:let's start|now let's|next let's|let's move on)",
        r"(?:great|perfect|excellent|awesome) [,.\-]?(?:let's|now|good)",
    ]

    # === CONFIDENCE MIRAGE PATTERNS ===
    # Success/affirmation language followed by error indicators
    CONFIDENCE_MIRAGE_PATTERNS = [
        (
            r"(?:done|finished|complete|all set|ready to go|no problem|success)(?:.{0,200})(?:error|failed|exception|timeout|400|500)",
            0.8,
        ),
        (
            r"(?:looks? good|all set|perfect|no issue)(?:.{0,100})(?:error|failed|exception)",
            0.75,
        ),
    ]

    # === SILENT FAILURE MASKING PATTERNS ===
    # Positive acknowledgment masking underlying failures
    SILENT_FAILURE_PATTERNS = [
        (
            r"(?:success|done|no problem|okay|alright)(?:.{0,100})(?:error|failed|exception|400|500)",
            0.8,
        ),
        (
            r"(?:(?:don|don\x27)t worry|no worries|nothing to worry about)(?:.{0,100})(?:error|failed|exception|problem)",
            0.7,
        ),
    ]

    # === EXCESSIVE BREADCRUMBS PATTERNS ===
    # Multiple single-line comments in sequence (hiding rather than explaining)
    EXCESSIVE_BREADCRUMBS_PATTERNS = [
        (r"#[^\n]*\n#[^\n]*\n#[^\n]*", 0.7),  # Three single-line comments in sequence
        (r"//[^\n]*\n//[^\n]*\n//[^\n]*", 0.7),  # Three JS-style comments in sequence
    ]

    # === REASONING-ACTION MISMATCH PATTERNS ===
    # User expresses expectation of success but tool actually failed
    # These are caught by cross-referencing tool_result success/failure state
    REASONING_ACTION_PATTERNS = [
        (r"but you (?:said|claimed|told me) (?:it (?:was|worked|finished|succeeded)|the (?:file|command|script) (?:was|is|would be))", 0.85),
        (r"but you said (?:it was|that it|you'd|you would)", 0.8),
        (r"but (?:it didn't|that didn't|you didn't) (?:work|finish|succeed|happen)", 0.75),
        (r"(?:I thought|thought) (?:it was|that) (?:done|finished|working)", 0.65),
    ]

    # Error keyword patterns in tool_result content
    _ERROR_INDICATORS = [
        "error:",
        "failed",
        "exception",
        "traceback",
        "exit code 1",
        "exit code 2",
        "does not exist",
        "file does not exist",
        "directory does not exist",
        "timeout",
        "timed out",
        "permission denied",
        "no such file",
        "command not found",
        "unexpected eof",
        "connection refused",
    ]

    def __init__(self, project_root: Path | None = None):
        """Initialize detector.

        Args:
            project_root: Project root directory (defaults to cwd)
        """
        self.project_root = project_root or Path.cwd()
        self.tool_use_map: dict[int, dict] = {}  # turn_num -> {tool_name, tool_id, success, error_content}

    def detect(
        self,
        transcript_path: Path | None,
        _terminal_id: str | None = None,  # type: ignore[unused-argument] — reserved for cross-session correlation
    ) -> SuspicionResult:
        """
        Detect suspicious patterns from conversation transcript.

        Args:
            transcript_path: Path to current session transcript JSONL
            terminal_id: Terminal identifier (reserved for future cross-session correlation)

        Returns:
            SuspicionResult with all detected suspicion items
        """
        items: list[SuspicionItem] = []

        if not transcript_path or not transcript_path.exists():
            return SuspicionResult(items=[], total_count=0)

        try:
            with open(transcript_path) as f:
                lines = f.readlines()
        except (OSError, PermissionError):
            return SuspicionResult(items=[], total_count=0)

        completion_re = re.compile("|".join(self.COMPLETION_SIGNALS), re.IGNORECASE)

        # Parse all messages for context
        messages: list[dict] = []
        for turn_num, line in enumerate(lines, start=1):
            try:
                message = json.loads(line)
                messages.append({"turn_num": turn_num, "msg": message})
            except json.JSONDecodeError:
                continue

        # Phase 1: Extract tool calls and results for reasoning-action mismatch detection
        self._extract_tool_calls(messages)

        # Scan each message
        for idx, entry in enumerate(messages):
            turn_num = entry["turn_num"]
            message = entry["msg"]
            content = message.get("content", "")
            role = message.get("role", "")

            # Skip system messages and very short content
            if role == "system" or len(content.strip()) < 15:
                continue

            # Skip if content has strong completion signals (item was likely resolved)
            if completion_re.search(content):
                continue

            prior_context = ""
            if idx > 0:
                prev_msg = messages[idx - 1]["msg"]
                prior_context = prev_msg.get("content", "")[:150]

            # Check each pattern category
            items.extend(self._check_contradictions(content, turn_num, prior_context))
            items.extend(self._check_reversals(content, turn_num, prior_context))
            items.extend(self._check_confusion(content, turn_num, prior_context))
            items.extend(
                self._check_resigned_acceptance(content, turn_num, prior_context, messages, idx)
            )
            items.extend(self._check_misalignment(content, turn_num, prior_context))
            # Phase 3: Heuristic classifiers
            items.extend(self._check_confidence_mirage(content, turn_num, prior_context))
            items.extend(self._check_silent_failure_masking(content, turn_num, prior_context))
            items.extend(self._check_excessive_breadcrumbs(content, turn_num, prior_context))
            # Phase 1: Reasoning-action mismatch detection (requires tool call context)
            items.extend(self._check_reasoning_action_mismatch(content, turn_num, prior_context))

        # Phase 4: Turn-position weighting for early-session commitments
        total_turns = len(messages)
        early_threshold = max(1, int(total_turns * 0.2))
        for item in items:
            if item.turn_number <= early_threshold and item.category in (
                "commitment_reversal",
                "misalignment",
            ):
                item.confidence = min(1.0, item.confidence + 0.1)

        # Deduplicate by normalized content
        items = self._deduplicate(items)

        return SuspicionResult(items=items, total_count=len(items))

    def _check_patterns(
        self,
        content: str,
        turn_num: int,
        prior_context: str,
        patterns: list[tuple[str, float]],
        category: Literal[
            "contradiction",
            "unresolved_confusion",
            "commitment_reversal",
            "misalignment",
            "confidence_mirage",
            "silent_failure_masking",
            "excessive_breadcrumbs",
        ],
    ) -> list[SuspicionItem]:
        """Check content against a set of regex patterns and build suspicion items."""
        items = []
        for pattern, confidence in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                items.append(
                    SuspicionItem(
                        category=category,
                        content=match.group(0).strip(),
                        turn_number=turn_num,
                        confidence=confidence,
                        source_message=content[:300],
                        prior_context=prior_context,
                    )
                )
        return items

    def _check_contradictions(
        self, content: str, turn_num: int, prior_context: str
    ) -> list[SuspicionItem]:
        """Check for contradiction patterns."""
        return self._check_patterns(
            content, turn_num, prior_context, self.CONTRADICTION_PATTERNS, "contradiction"
        )

    def _check_reversals(
        self, content: str, turn_num: int, prior_context: str
    ) -> list[SuspicionItem]:
        """Check for commitment reversal patterns."""
        return self._check_patterns(
            content, turn_num, prior_context, self.REVERSAL_PATTERNS, "commitment_reversal"
        )

    def _check_confusion(
        self, content: str, turn_num: int, prior_context: str
    ) -> list[SuspicionItem]:
        """Check for expressed confusion patterns."""
        return self._check_patterns(
            content, turn_num, prior_context, self.CONFUSION_PATTERNS, "unresolved_confusion"
        )

    def _check_resigned_acceptance(
        self,
        content: str,
        turn_num: int,
        prior_context: str,
        messages: list[dict],
        idx: int,
    ) -> list[SuspicionItem]:
        """Check for resigned acceptance patterns.

        Resigned acceptance is when user accepts something despite
        a prior concern. We look for acceptance patterns in current
        message + concern patterns in the prior 2 messages.
        """
        # Find any acceptance pattern match first
        acceptance_match = None
        for pattern, _ in self.RESIGNED_PATTERNS:
            m = re.search(pattern, content, re.IGNORECASE)
            if m:
                acceptance_match = m
                break

        if not acceptance_match:
            return []

        # Check prior messages for expressed concerns
        concern_keywords = [
            "confused",
            "don't understand",
            "not sure",
            "wait",
            "no wait",
            "actually",
            "that doesn't make sense",
            "something's wrong",
            "this is wrong",
            "I'm not",
        ]

        prior_turns = messages[max(0, idx - 2) : idx]
        has_prior_concern = any(
            any(kw.lower() in str(m["msg"].get("content", "")).lower() for kw in concern_keywords)
            for m in prior_turns
        )

        if has_prior_concern:
            return [
                SuspicionItem(
                    category="resigned_acceptance",
                    content=acceptance_match.group(0).strip(),
                    turn_number=turn_num,
                    confidence=0.75,
                    source_message=content[:300],
                    prior_context=prior_context,
                )
            ]
        return []

    def _check_misalignment(
        self, content: str, turn_num: int, prior_context: str
    ) -> list[SuspicionItem]:
        """Check for misalignment patterns."""
        return self._check_patterns(
            content, turn_num, prior_context, self.MISALIGNMENT_PATTERNS, "misalignment"
        )

    def _check_confidence_mirage(
        self, content: str, turn_num: int, prior_context: str
    ) -> list[SuspicionItem]:
        """Check for confidence mirage patterns (success language masking failures)."""
        return self._check_patterns(
            content, turn_num, prior_context, self.CONFIDENCE_MIRAGE_PATTERNS, "confidence_mirage"
        )

    def _check_silent_failure_masking(
        self, content: str, turn_num: int, prior_context: str
    ) -> list[SuspicionItem]:
        """Check for silent failure masking patterns."""
        return self._check_patterns(
            content, turn_num, prior_context, self.SILENT_FAILURE_PATTERNS, "silent_failure_masking"
        )

    def _check_excessive_breadcrumbs(
        self, content: str, turn_num: int, prior_context: str
    ) -> list[SuspicionItem]:
        """Check for excessive breadcrumbs (multiple comments hiding rather than explaining)."""
        return self._check_patterns(
            content, turn_num, prior_context, self.EXCESSIVE_BREADCRUMBS_PATTERNS, "excessive_breadcrumbs"
        )

    def _extract_tool_calls(self, messages: list[dict]) -> None:
        """Phase 1: Extract tool calls and results from transcript.

        Builds self.tool_use_map: turn_num -> {tool_name, tool_id, success, error_content}
        Success is determined by is_error flag or error keyword detection.
        """
        self.tool_use_map.clear()
        tool_id_to_turn: dict[str, int] = {}

        # First pass: extract all tool_use entries (assistant messages)
        for entry in messages:
            turn_num = entry["turn_num"]
            message = entry["msg"]
            role = message.get("role", "")
            content = message.get("content", "")

            if role != "assistant" or not content:
                continue

            # Handle content as a list of blocks
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_use":
                        tool_id = block.get("id", "")
                        tool_name = block.get("name", "")
                        tool_input = block.get("input") or {}
                        if isinstance(tool_input, dict):
                            # Store command/file context for success evaluation
                            command = tool_input.get("command", "")[:200] if tool_input.get("command") else ""
                            file_path = tool_input.get("file_path", "")[:200] if tool_input.get("file_path") else ""
                        else:
                            command = ""
                            file_path = ""
                        self.tool_use_map[turn_num] = {
                            "tool_name": tool_name,
                            "tool_id": tool_id,
                            "success": True,  # provisional — updated when tool_result arrives
                            "error_content": "",
                            "command": command,
                            "file_path": file_path,
                        }
                        if tool_id:
                            tool_id_to_turn[tool_id] = turn_num

        # Second pass: extract tool_result entries (user messages) and update success
        for entry in messages:
            turn_num = entry["turn_num"]
            message = entry["msg"]
            role = message.get("role", "")
            content = message.get("content", "")

            if role != "user" or not content:
                continue

            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_result":
                        tool_use_id = block.get("tool_use_id", "")
                        result_content = block.get("content", "") or ""
                        is_error = block.get("is_error", False)

                        # Determine if tool failed
                        failed = is_error
                        if not failed:
                            result_lower = result_content.lower()
                            failed = any(
                                err in result_lower for err in self._ERROR_INDICATORS
                            )

                        # Update the corresponding tool_use entry
                        src_turn = tool_id_to_turn.get(tool_use_id)
                        if src_turn is not None and src_turn in self.tool_use_map:
                            self.tool_use_map[src_turn]["success"] = not failed
                            self.tool_use_map[src_turn]["error_content"] = result_content[:500]

    def _check_reasoning_action_mismatch(
        self,
        content: str,
        turn_num: int,
        prior_context: str,
    ) -> list[SuspicionItem]:
        """Check for reasoning-action mismatch patterns.

        Detects when user expresses expectation of success but the tool actually failed.
        Requires tool_use_map to be populated by _extract_tool_calls.
        """
        items = []

        # Check text patterns first
        for pattern, confidence in self.REASONING_ACTION_PATTERNS:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                items.append(
                    SuspicionItem(
                        category="reasoning_action",
                        content=match.group(0).strip(),
                        turn_number=turn_num,
                        confidence=confidence,
                        source_message=content[:300],
                        prior_context=prior_context,
                    )
                )

        return items

    def _deduplicate(self, items: list[SuspicionItem]) -> list[SuspicionItem]:
        """Remove duplicate items based on content similarity."""
        if not items:
            return items

        def normalize(content: str) -> str:
            return re.sub(r"[^\w\s]", "", content.lower())[:80]

        seen: dict[str, SuspicionItem] = {}
        result: list[SuspicionItem] = []

        for item in items:
            key = normalize(item.content)
            if key not in seen:
                seen[key] = item
                result.append(item)
            else:
                # Keep the higher confidence one
                existing = seen[key]
                if item.confidence > existing.confidence:
                    seen[key] = item
                    for i, r in enumerate(result):
                        if normalize(r.content) == key:
                            result[i] = item
                            break

        return result


# Convenience function
def detect_suspicion(
    transcript_path: Path | None,
    terminal_id: str | None = None,
    project_root: Path | None = None,
) -> SuspicionResult:
    """
    Quick suspicion detection.

    Args:
        transcript_path: Path to current session transcript
        terminal_id: Terminal identifier
        project_root: Project root directory

    Returns:
        SuspicionResult with detected items
    """
    detector = SuspicionDetector(project_root)
    return detector.detect(transcript_path, terminal_id)
