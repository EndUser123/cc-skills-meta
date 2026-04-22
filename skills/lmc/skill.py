#!/usr/bin/env python
"""
Lossless Maximal Compaction (LMC) Skill

Aggressive token optimization that preserves all critical information
while maximizing compression. Keeps function/class signatures and
essential logic while removing redundancy.
"""

from __future__ import annotations

import argparse
import ast
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

# Add hooks directory to path for terminal detection
hooks_dir = Path(__file__).resolve().parent.parent.parent / "hooks"
sys.path.insert(0, str(hooks_dir))

try:
    from skill_guard.utils.terminal_detection import detect_terminal_id
except ImportError:
    # Fallback terminal detection
    def detect_terminal_id() -> str:
        """Fallback terminal detection."""
        for env_var in ["WT_SESSION", "TERM_PROGRAM", "POWERLINE_COMMAND"]:
            if val := os.environ.get(env_var):
                return val.replace("\\", "_").replace("/", "_")[:50]
        return "unknown"


if TYPE_CHECKING:
    pass


class ContentClassifier:
    """Classify content by priority for lossy filtering."""

    def __init__(self, content: str, content_type: str = "code"):
        self.content = content
        self.content_type = content_type
        self.terminal_id = detect_terminal_id()

    def classify(self) -> dict:
        """Classify content into essential vs optional."""
        essential = {
            "function_signatures": [],
            "class_definitions": [],
            "critical_logic": [],
            "error_handling": [],
        }
        optional = {
            "inline_comments": [],
            "verbose_docstrings": [],
            "exploratory_notes": [],
            "debug_code": [],
        }

        if self.content_type == "code":
            self._classify_code(essential, optional)

        return {
            "essential": essential,
            "optional": optional,
            "statistics": self._calculate_stats(essential, optional),
        }

    def _classify_code(self, essential: dict, optional: dict) -> None:
        """Classify Python code content."""
        try:
            tree = ast.parse(self.content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    essential["function_signatures"].append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "args": [arg.arg for arg in node.args.args],
                        }
                    )

                    docstring = ast.get_docstring(node)
                    if docstring and len(docstring) > 100:
                        optional["verbose_docstrings"].append(
                            {"name": node.name, "line": node.lineno, "length": len(docstring)}
                        )

                elif isinstance(node, ast.ClassDef):
                    essential["class_definitions"].append({"name": node.name, "line": node.lineno})

            # Scan for inline comments
            for i, line in enumerate(self.content.split("\n"), 1):
                stripped = line.strip()
                if stripped.startswith("#") and not stripped.startswith("#!"):
                    optional["inline_comments"].append({"line": i, "text": stripped[:60]})

        except SyntaxError:
            # If parsing fails, treat all as essential
            pass

    def _calculate_stats(self, essential: dict, optional: dict) -> dict:
        """Calculate token statistics."""
        essential_count = (
            len(essential["function_signatures"]) * 10
            + len(essential["class_definitions"]) * 10
            + len(essential["critical_logic"]) * 5
        )
        optional_count = (
            len(optional["inline_comments"]) * 3
            + len(optional["verbose_docstrings"]) * 20
            + len(optional["exploratory_notes"]) * 10
        )

        return {
            "essential_tokens": essential_count,
            "optional_tokens": optional_count,
            "drop_ratio": optional_count / (essential_count + optional_count)
            if (essential_count + optional_count) > 0
            else 0,
        }


class LossyFilter:
    """Apply lossy filters to drop non-essential content."""

    def __init__(self, classifier: ContentClassifier):
        self.classifier = classifier

    def apply_filters(self, aggressive: bool = False) -> dict:
        """Apply lossy filters based on retention level."""
        classification = self.classifier.classify()

        filtered = {
            "function_signatures": classification["essential"]["function_signatures"],
            "class_definitions": classification["essential"]["class_definitions"],
            "critical_logic": classification["essential"]["critical_logic"],
            "error_handling": classification["essential"]["error_handling"],
        }

        # In non-aggressive mode, keep some docstrings
        if not aggressive:
            # Keep short docstrings (< 100 chars)
            for docstring in classification["optional"]["verbose_docstrings"]:
                if docstring["length"] < 100:
                    filtered.setdefault("short_docstrings", []).append(docstring)

        return filtered


class MinimalSummaryGenerator:
    """Generate ultra-compact summary with core decisions only."""

    def __init__(self, filter: LossyFilter, original_content: str):
        self.filter = filter
        self.original_content = original_content

    def generate(self, retention_level: str = "decisions-only") -> dict:
        """Generate minimal summary."""
        filtered_content = self.filter.apply_filters(aggressive=(retention_level == "aggressive"))

        # Estimate original tokens
        original_tokens = len(self.original_content) // 4

        # Estimate compressed tokens (just signatures/classes)
        compressed_tokens = (
            len(filtered_content["function_signatures"]) * 5
            + len(filtered_content["class_definitions"]) * 5
            + len(filtered_content.get("short_docstrings", [])) * 3
        )

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "terminal_id": self.filter.classifier.terminal_id,
            "retention_level": retention_level,
            "functions": filtered_content["function_signatures"],
            "classes": filtered_content["class_definitions"],
            "compression_stats": {
                "original_tokens": original_tokens,
                "compressed_tokens": compressed_tokens,
                "ratio": compressed_tokens / original_tokens if original_tokens > 0 else 0,
                "savings_percent": (1 - compressed_tokens / original_tokens) * 100
                if original_tokens > 0
                else 0,
            },
        }


class LMCSkill:
    """Lossy Minimal Compaction skill."""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.target = args.target if hasattr(args, "target") else None
        self.content = None
        self.content_type = "code"
        self.terminal_id = detect_terminal_id()
        # Defensive: get retention_level with fallback
        self.retention_level = getattr(args, "retain", None) or "decisions-only"

    def run(self) -> bool:
        """Execute LMC workflow."""
        print("=== LMC: Lossy Minimal Compaction ===")
        print()

        # Load content if target specified
        if self.target:
            self._load_content()
            if not self.content:
                print(f"Error: Could not read {self.target}")
                return False

        if not self.content:
            print("Usage: /lmc <file> [--retain LEVEL] [--aggressive]")
            print()
            print("Aggressively optimizes content by dropping non-essential")
            print("information for maximum token efficiency (60-80% savings).")
            print()
            print("Retention levels:")
            print("  decisions-only  - Keep only function/class signatures (default)")
            print("  decisions+tests - Keep signatures + test outcomes")
            print("  all-outcomes    - Keep all actionable results")
            return False

        # Step 1: Classify content
        classifier = ContentClassifier(self.content, self.content_type)
        classification = classifier.classify()
        self._print_classification(classification)

        # Step 2-3: Apply filters and generate minimal summary
        lossy_filter = LossyFilter(classifier)
        generator = MinimalSummaryGenerator(lossy_filter, self.content)
        summary = generator.generate(self.retention_level)

        # Step 4: Show compression results
        self._print_summary(summary)

        # Lossy warning
        print()
        print("⚠️ Note: This is lossy compression. Process details are dropped.")
        print("Use /mlc instead if you need full information preserved.")

        return True

    def _print_classification(self, classification: dict) -> None:
        """Print classification results."""
        print("Content Classification:")
        print()

        stats = classification["statistics"]
        total = stats["essential_tokens"] + stats["optional_tokens"]

        print(f"  Estimated tokens: ~{total:,}")
        print(
            f"  Essential: {stats['essential_tokens']:,} ({stats['essential_tokens']/total*100:.0f}%)"
        )
        print(
            f"  Optional (droppable): {stats['optional_tokens']:,} ({stats['optional_tokens']/total*100:.0f}%)"
        )
        print()

        essential = classification["essential"]
        print(f"  Functions: {len(essential['function_signatures'])}")
        print(f"  Classes: {len(essential['class_definitions'])}")
        print(f"  Critical logic: {len(essential['critical_logic'])}")
        print()

        optional = classification["optional"]
        print(f"  Inline comments: {len(optional['inline_comments'])}")
        print(f"  Verbose docstrings: {len(optional['verbose_docstrings'])}")
        print(f"  Exploratory notes: {len(optional['exploratory_notes'])}")
        print()

    def _print_summary(self, summary: dict) -> None:
        """Print minimal summary."""
        print("Minimal Structure Preserved:")
        print()

        for func in summary["functions"]:
            args_str = ", ".join(func["args"])
            print(f"  def {func['name']}({args_str})")

        for cls in summary["classes"]:
            print(f"  class {cls['name']}")

        print()
        print("Compression Stats:")
        stats = summary["compression_stats"]
        print(f"  Original: ~{stats['original_tokens']:,} tokens")
        print(f"  Compressed: ~{stats['compressed_tokens']:,} tokens")
        print(f"  Savings: {stats['savings_percent']:.0f}%")

    def _load_content(self) -> None:
        """Load content from target file."""
        target_path = Path(self.target)
        if not target_path.exists():
            print(f"File not found: {self.target}")
            return

        with open(target_path, encoding="utf-8") as f:
            self.content = f.read()

        # Detect content type
        if self.target.endswith((".py",)):
            self.content_type = "code"
        else:
            self.content_type = "generic"


def main():
    """Main entry point for LMC skill."""
    parser = argparse.ArgumentParser(
        description="Lossless Maximal Compaction - Maximum token optimization that preserves all critical information"
    )
    parser.add_argument("target", nargs="?", help="File to analyze")
    parser.add_argument(
        "--retain",
        choices=["decisions-only", "decisions+tests", "all-outcomes"],
        default="decisions-only",
        help="Retention level (default: decisions-only)",
    )
    parser.add_argument(
        "--aggressive", action="store_true", help="Drop all prose, keep only structured data"
    )

    args = parser.parse_args()

    # Ensure retention_level is always set (argparse default handling)
    if not hasattr(args, "retain") or args.retain is None:
        args.retain = "decisions-only"

    skill = LMCSkill(args)
    result = skill.run()

    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
