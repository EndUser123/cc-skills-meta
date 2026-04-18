"""Session Chain Analyzer - LLM-powered analysis of session chain transcripts."""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _kill_process_after_delay(proc: subprocess.Popen, timeout_seconds: int) -> None:
    """Kill process if it doesn't complete within timeout.

    This runs in a separate thread and kills the process if the main thread
    doesn't complete in time. Used to enforce timeout on process creation.
    """
    import time
    time.sleep(timeout_seconds)
    if proc.poll() is None:  # Process still running
        try:
            proc.kill()
        except OSError:
            pass


@dataclass
class ChainAnalysisResult:
    """Result of session chain analysis."""
    focus: str
    phase: str
    next_steps: list[str]
    confidence: float
    error: str | None = None
    transcripts_processed: int = 0


class SessionChainAnalyzer:
    """Analyze session chain transcripts using a subagent."""

    CRITIQUE_GRADING_PROMPT = (
        "Grade the subagent analysis as PASS or FAIL. "
        "PASS if findings are specific, grounded in transcript evidence, and answer the query. "
        "FAIL if vague, generic, or contradicted by transcript content."
    )

    MAX_CHAIN_DEPTH = 10
    MAX_INPUT_TOKENS_PER_TRANSCRIPT = 2000
    SUBAGENT_TIMEOUT_SECONDS = 50
    CRITIQUE_TIMEOUT_SECONDS = 10

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()

    def analyze(
        self,
        transcript_paths: list[Path],
        query: str | None = None,
    ) -> ChainAnalysisResult:
        """Analyze session chain using a subagent.

        Args:
            transcript_paths: List of transcript paths (oldest to current)
            query: Optional query to focus the analysis

        Returns:
            ChainAnalysisResult with focus, phase, next_steps, confidence
        """
        if not transcript_paths:
            return ChainAnalysisResult(
                focus="",
                phase="",
                next_steps=[],
                confidence=0.0,
                error="no_transcripts",
                transcripts_processed=0,
            )

        # Validate paths before passing to subagent (defense in depth)
        validated_paths = self._validate_paths(transcript_paths)
        if not validated_paths:
            return ChainAnalysisResult(
                focus="",
                phase="",
                next_steps=[],
                confidence=0.0,
                error="invalid_paths",
                transcripts_processed=0,
            )

        # Build analysis prompt
        prompt = self._build_analysis_prompt(validated_paths, query)

        # Grant subagent read access to transcript directories
        add_dirs = list({p.parent for p in validated_paths})

        # Run subagent - timeout governed by orchestrator's 300s subprocess limit
        try:
            result_json = self._run_subagent(
                prompt, add_dirs=add_dirs
            )
            return self._parse_result(result_json, len(validated_paths))
        except TimeoutError:
            logger.warning("Subagent timed out after 300s")
            return ChainAnalysisResult(
                focus="",
                phase="",
                next_steps=[],
                confidence=0.0,
                error="timeout",
                transcripts_processed=len(validated_paths),
            )

    def _validate_paths(
        self, paths: list[Path], max_size_mb: float = 50.0
    ) -> list[Path]:
        """Validate all paths are within allowed transcript directory.

        Defense in depth: re-validate paths before passing to subagent.
        Rejects paths with .. escape sequences or absolute paths outside transcript dir.
        Enforces configurable file size limit per transcript (default 10MB).
        """
        validated = []
        for p in paths:
            try:
                resolved = p.resolve()
                # Check within sessions directory
                sessions_dir = Path.home() / ".claude" / "projects"
                if not resolved.is_relative_to(sessions_dir.resolve()):
                    logger.warning("Path outside sessions dir rejected: %s", p)
                    continue
                # Check for symlinks (could escape via symlink to outside sessions dir)
                if p.is_symlink():
                    logger.warning("Symlink rejected: %s", p)
                    continue
                # Check for .. escape
                if ".." in str(p):
                    logger.warning("Path with .. escape rejected: %s", p)
                    continue
                # Check file size (configurable limit, default 10MB)
                if resolved.exists() and resolved.stat().st_size > max_size_mb * 1024 * 1024:
                    logger.warning("File too large (>%dMB): %s", max_size_mb, p)
                    continue
                validated.append(p)
            except Exception as e:
                logger.warning("Path validation error for %s: %s", p, e)
                continue
        return validated

    def _build_analysis_prompt(
        self, paths: list[Path], query: str | None
    ) -> str:
        """Build the analysis prompt for the subagent."""
        query_section = ""
        if query:
            query_section = f"\nUser query: {query}\n"

        prompt = f"""Read each transcript file and analyze the session chain to answer:

1. What was the session chain focused on? (work type, domain)
2. What phase/stage was reached?
3. What was identified as needing to happen next?
{query_section}
Transcripts to analyze (oldest to current):
{chr(10).join(f"- {p}" for p in paths)}

Output your analysis as JSON with this exact structure:
{{
  "focus": "What the session chain was focused on",
  "phase": "Current phase/stage reached",
  "next_steps": ["step1", "step2", "step3"],
  "confidence": 0.0-1.0
}}

If a transcript is empty or unreadable, note it in the focus field.
If you cannot determine the phase, use "unknown".
Be specific and grounded in the transcript evidence.
"""
        return prompt

    def _run_subagent(
        self, prompt: str, add_dirs: list[Path] | None = None
    ) -> dict[str, Any]:
        """Run the subagent via claude -p subprocess.

        Uses subprocess.Popen with claude -p to perform LLM analysis.
        This avoids depending on the Agent tool being available in the caller's context.

        Timeout is governed by the SUBAGENT_TIMEOUT_SECONDS class variable.
        """
        agent_prompt = prompt
        if add_dirs:
            dir_list = ", ".join(str(d) for d in add_dirs)
            agent_prompt = (
                f"Access to the following directories is available for reading transcript files:\n"
                f"{dir_list}\n\n---\n\n{prompt}"
            )

        try:
            # Find claude executable
            claude_cmd = shutil.which("claude")
            if not claude_cmd:
                raise RuntimeError("claude command not found in PATH")

            # Create process with timeout protection
            proc = subprocess.Popen(
                [claude_cmd, "-p", agent_prompt],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.project_root),
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0,
            )

            # Start timeout thread to enforce timeout during process creation
            timeout_thread = threading.Thread(
                target=_kill_process_after_delay,
                args=(proc, self.SUBAGENT_TIMEOUT_SECONDS),
                daemon=True,
            )
            timeout_thread.start()

            try:
                stdout, stderr = proc.communicate(timeout=self.SUBAGENT_TIMEOUT_SECONDS)
                # Cancel the timeout thread since we completed successfully
                timeout_thread.join(timeout=0.1)
            except subprocess.TimeoutExpired:
                # Wait for timeout thread to complete (should have killed process)
                timeout_thread.join(timeout=1.0)
                raise

            stdout_text = stdout.decode("utf-8", errors="replace")

            if proc.returncode not in (0, 1):
                stderr_text = stderr.decode("utf-8", errors="replace")[:200]
                logger.warning("Subagent exited with code %d: %s", proc.returncode, stderr_text)
                raise RuntimeError(f"Subagent failed with exit code {proc.returncode}")

            return self._extract_json(stdout_text)

        except subprocess.TimeoutExpired:
            logger.warning("Subagent timed out after %ds", self.SUBAGENT_TIMEOUT_SECONDS)
            raise TimeoutError(f"Subagent timed out after {self.SUBAGENT_TIMEOUT_SECONDS}s")
        except Exception as e:
            logger.warning("_run_subagent failed: %s", e)
            raise

    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from subagent output.

        Raises ValueError if no valid JSON is found, rather than returning
        a false default dict that masks parse failures.
        """
        import re

        # Anchor to first { and match greedily to capture
        # a single complete JSON object (handles nested braces)
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError as e:
                logger.warning("JSON block parse failed: %s", e)
                raise ValueError(f"Invalid JSON in subagent output: {e}") from e

        # Try whole text as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning("Full text parse failed: %s", e)
            raise ValueError(f"Subagent output is not valid JSON: {e}") from e

    def _parse_result(
        self, result_json: dict[str, Any], transcripts_count: int
    ) -> ChainAnalysisResult:
        """Parse subagent JSON result into ChainAnalysisResult."""
        return ChainAnalysisResult(
            focus=result_json.get("focus", ""),
            phase=result_json.get("phase", ""),
            next_steps=result_json.get("next_steps", []),
            confidence=float(result_json.get("confidence", 0.0)),
            error=None,
            transcripts_processed=transcripts_count,
        )

    def critique_grade(
        self, analysis: ChainAnalysisResult, chain_result: Any | None = None
    ) -> tuple[str, str | None]:
        """Grade the analysis as PASS or FAIL with specific feedback.

        Args:
            analysis: The analysis result to grade
            _transcript_paths: Deprecated, unused (kept for backward compatibility)

        Returns:
            Tuple of (grade, feedback). feedback is None if PASS.
        """
        if analysis.error:
            return "FAIL", f"Analysis returned error: {analysis.error}"

        # Check minimum viability
        if not analysis.focus and not analysis.next_steps:
            return "FAIL", "Analysis is empty or vague. Provide specific focus and next steps."

        if analysis.confidence < 0.3:
            return "FAIL", f"Confidence too low ({analysis.confidence:.2f}). Analysis may be unreliable."

        # Build critique prompt
        prompt = f"""{self.CRITIQUE_GRADING_PROMPT}

Analysis to grade:
- Focus: {analysis.focus}
- Phase: {analysis.phase}
- Next steps: {', '.join(analysis.next_steps) if analysis.next_steps else 'none'}
- Confidence: {analysis.confidence:.2f}

Output your grade as JSON:
{{"grade": "PASS" or "FAIL", "feedback": "specific feedback if FAIL"}}
"""

        try:
            result_json = self._run_subagent(prompt)
            grade = result_json.get("grade", "FAIL")
            feedback = result_json.get("feedback")
            if grade == "PASS":
                feedback = None
            return grade, feedback
        except Exception:
            # On critique failure, default to PASS with available results
            return "PASS", None

    # -------------------------------------------------------------------------
    # ChainWalkResult-based methods (uses history.jsonl via search-research)
    # -------------------------------------------------------------------------

    def _message_preview(self, msg: str | dict | None, max_len: int = 200) -> str:
        """Extract a short preview string from a message field."""
        if msg is None:
            return ""
        if isinstance(msg, str):
            return msg[:max_len] + ("..." if len(msg) > max_len else "")
        if isinstance(msg, dict):
            content = msg.get("content")
            if isinstance(content, list):
                parts = []
                for block in content:
                    if isinstance(block, dict):
                        text = block.get("content") or block.get("text", "")
                        if isinstance(text, str):
                            parts.append(text[:100])
                return " | ".join(parts)[:max_len] + ("..." if sum(len(p) for p in parts) > max_len else "")
            return str(content)[:max_len] if content else ""

    def _read_transcript_for_entry(self, entry: Any) -> str | None:
        """Read actual transcript content from an entry's transcript_path.

        Supports both SessionChainEntry (search-research) and dict formats.
        Returns None if entry has no transcript_path or file cannot be read.
        """
        # Try SessionChainEntry attribute first, then dict key
        transcript_path = getattr(entry, "transcript_path", None) or entry.get("transcriptPath")

        if not transcript_path:
            return None

        try:
            path = Path(transcript_path)
            if path.exists() and path.is_file():
                # Read with size limit (first 2000 tokens)
                content = path.read_text(encoding="utf-8")
                return content[: self.MAX_INPUT_TOKENS_PER_TRANSCRIPT * 4]  # ~4 chars/token
        except Exception as e:
            logger.warning("Failed to read transcript %s: %s", transcript_path, e)

        return None

    def _build_chain_result_prompt(
        self, entries: list, query: str | None
    ) -> str:
        """Build analysis prompt from ChainEntry objects (not file paths).

        Reads actual transcript files via transcript_path to provide real
        conversation content, not just metadata summaries.
        """
        query_section = ""
        if query:
            query_section = f"\nUser query: {query}\n"

        entry_lines: list[str] = []
        for i, entry in enumerate(entries):
            # Support both ChainEntry (search-research) and dict (raw) formats
            entry_type = getattr(entry, "entry_type", None) or entry.get("type", "unknown")
            session_id = getattr(entry, "session_id", None) or entry.get("sessionId", "?")
            summary = getattr(entry, "summary", None) or entry.get("summary")
            message = getattr(entry, "message", None) or entry.get("message")
            is_origin = getattr(entry, "is_origin", False) or entry.get("is_origin", False)

            # Try to read actual transcript content
            transcript_content = self._read_transcript_for_entry(entry)

            if transcript_content:
                # Truncate to 500 chars to stay within claude -p token limits
                # when multiple entries are combined in the prompt
                content = f"[transcript]\n{transcript_content[:500]}"
            elif entry_type == "summary" and summary:
                # Fallback to summary if no transcript available
                content = f"[summary] {summary}"
            else:
                # Last resort: message preview
                content = self._message_preview(message)

            marker = " (ORIGIN)" if is_origin else ""
            entry_lines.append(f"[{i}] session={session_id[:8]}, type={entry_type}{marker}:\n{content}")

        prompt = f"""Read the session chain entries below and analyze the chain to answer:

1. What was the session chain focused on? (work type, domain)
2. What phase/stage was reached?
3. What was identified as needing to happen next?
{query_section}
Session chain entries (oldest to current):
{chr(10).join(entry_lines)}

Output your analysis as JSON with this exact structure:
{{
  "focus": "What the session chain was focused on",
  "phase": "Current phase/stage reached",
  "next_steps": ["step1", "step2", "step3"],
  "confidence": 0.0-1.0
}}

If you cannot determine the phase, use "unknown".
Be specific and grounded in the entry evidence.
"""
        return prompt

    def analyze_chain_result(
        self,
        chain_result: Any,
        query: str | None = None,
    ) -> ChainAnalysisResult:
        """Analyze session chain from a ChainWalkResult object.

        Args:
            chain_result: ChainWalkResult from search-research.history_chain
            query: Optional query to focus the analysis

        Returns:
            ChainAnalysisResult with focus, phase, next_steps, confidence
        """
        entries = getattr(chain_result, "entries", None) or []
        if not entries:
            return ChainAnalysisResult(
                focus="",
                phase="",
                next_steps=[],
                confidence=0.0,
                error="no_transcripts",
                transcripts_processed=0,
            )

        try:
            prompt = self._build_chain_result_prompt(entries, query)
            result_json = self._run_subagent(prompt)
            return self._parse_result(result_json, len(entries))
        except TimeoutError:
            logger.warning("Chain result subagent timed out after 300s")
            return ChainAnalysisResult(
                focus="",
                phase="",
                next_steps=[],
                confidence=0.0,
                error="timeout",
                transcripts_processed=len(entries),
            )
        except Exception as e:
            logger.warning("Chain result analysis failed: %s", e)
            return ChainAnalysisResult(
                focus="",
                phase="",
                next_steps=[],
                confidence=0.0,
                error="crash",
                transcripts_processed=len(entries),
            )

    def critique_grade_chain_result(
        self,
        analysis: ChainAnalysisResult,
        chain_result: Any,
    ) -> tuple[str, str | None]:
        """Grade the analysis using ChainWalkResult (for critique agent context).

        Args:
            analysis: The analysis result to grade
            chain_result: ChainWalkResult for context

        Returns:
            Tuple of (grade, feedback). feedback is None if PASS.
        """
        if analysis.error:
            return "FAIL", f"Analysis returned error: {analysis.error}"

        # Check minimum viability
        if not analysis.focus and not analysis.next_steps:
            return "FAIL", "Analysis is empty or vague. Provide specific focus and next steps."

        if analysis.confidence < 0.3:
            return "FAIL", f"Confidence too low ({analysis.confidence:.2f}). Analysis may be unreliable."

        # Build critique prompt using chain entry context
        entries = getattr(chain_result, "entries", None) or []
        entry_summaries = []
        for entry in entries[:5]:  # Use first 5 entries for context
            entry_type = getattr(entry, "entry_type", None) or entry.get("type", "?")
            summary = getattr(entry, "summary", None) or entry.get("summary")
            msg = getattr(entry, "message", None) or entry.get("message")
            if summary:
                entry_summaries.append(f"[{entry_type}] {summary[:80]}")
            else:
                entry_summaries.append(f"[{entry_type}] {self._message_preview(msg, 80)}")

        entries_context = chr(10).join(entry_summaries) if entry_summaries else "no entries"

        prompt = f"""{self.CRITIQUE_GRADING_PROMPT}

Analysis to grade:
- Focus: {analysis.focus}
- Phase: {analysis.phase}
- Next steps: {', '.join(analysis.next_steps) if analysis.next_steps else 'none'}
- Confidence: {analysis.confidence:.2f}

Chain entry context (first 5):
{entries_context}

Output your grade as JSON:
{{"grade": "PASS" or "FAIL", "feedback": "specific feedback if FAIL"}}
"""

        try:
            result_json = self._run_subagent(prompt)
            grade = result_json.get("grade", "FAIL")
            feedback = result_json.get("feedback")
            if grade == "PASS":
                feedback = None
            return grade, feedback
        except Exception:
            return "PASS", None

    def _rerun_from_chain_result(
        self,
        chain_result: Any,
        query: str | None,
        feedback: str | None,
    ) -> dict[str, Any]:
        """Rerun chain analysis with critique feedback using ChainWalkResult."""
        entries = getattr(chain_result, "entries", None) or []
        entry_lines = []
        for i, entry in enumerate(entries):
            entry_type = getattr(entry, "entry_type", None) or entry.get("type", "unknown")
            session_id = getattr(entry, "session_id", None) or entry.get("sessionId", "?")
            summary = getattr(entry, "summary", None) or entry.get("summary")
            message = getattr(entry, "message", None) or entry.get("message")
            is_origin = getattr(entry, "is_origin", False) or entry.get("is_origin", False)

            # Try to read actual transcript content
            transcript_content = self._read_transcript_for_entry(entry)

            if transcript_content:
                # Truncate to 500 chars to stay within claude -p token limits
                # when multiple entries are combined in the prompt
                content = f"[transcript]\n{transcript_content[:500]}"
            elif entry_type == "summary" and summary:
                # Fallback to summary if no transcript available
                content = f"[summary] {summary}"
            else:
                # Last resort: message preview
                content = self._message_preview(message)

            marker = " (ORIGIN)" if is_origin else ""
            entry_lines.append(f"[{i}] session={session_id[:8]}, type={entry_type}{marker}: {content}")

        query_section = ""
        if query:
            query_section = f"\nUser query: {query}\n"

        prompt = f"""You previously analyzed the session chain but your analysis was incomplete.

Your prior analysis had these issues:
{feedback}

Please re-read the session chain entries below and provide a corrected analysis that:
1. Addresses the specific issues mentioned above
2. Is specific and grounded in entry evidence
3. Answers: What was focused on? What phase/stage? What needs to happen next?
{query_section}Session chain entries (oldest to current):
{chr(10).join(entry_lines)}

Output as JSON with focus, phase, next_steps, confidence.
"""
        return self._run_subagent(prompt)


def analyze_session_chain(
    transcript_paths: list[Path],
    query: str | None = None,
    project_root: Path | None = None,
) -> ChainAnalysisResult:
    """Quick entry point for session chain analysis."""
    analyzer = SessionChainAnalyzer(project_root)
    return analyzer.analyze(transcript_paths, query)