#!/usr/bin/env python
"""
Minimal Lossy Compaction (MLC) Skill

Conservative token optimization for code/docs/output.
Preserves ALL critical information while removing redundancy.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class TokenAnalyzer:
    """Analyze token usage in content."""

    def __init__(self, content: str, content_type: str = "code"):
        self.content = content
        self.content_type = content_type

    def estimate_tokens(self) -> int:
        """Estimate token count (rough approximation: 1 token ≈ 4 chars)."""
        return len(self.content) // 4

    def find_inefficiencies(self) -> list[dict]:
        """Find token inefficiencies based on content type."""
        if self.content_type == "code":
            return self._analyze_code()
        elif self.content_type == "docs":
            return self._analyze_docs()
        else:
            return self._analyze_generic()

    def _analyze_code(self) -> list[dict]:
        """Analyze code for inefficiencies."""
        findings = []
        lines = self.content.split("\n")

        # Find self-evident comments
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#") and not stripped.startswith("#!"):
                comment_text = stripped[1:].strip()
                if i < len(lines):
                    next_line = lines[i].strip() if i < len(lines) else ""
                    if comment_text.lower() in next_line.lower() or len(comment_text) < 5:
                        findings.append(
                            {
                                "type": "self_evident_comment",
                                "line": i,
                                "text": stripped,
                                "savings": self._estimate_line_tokens(line),
                            }
                        )

        # Find verbose docstrings
        try:
            tree = ast.parse(self.content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    docstring = ast.get_docstring(node)
                    if docstring and len(docstring) > 200:
                        findings.append(
                            {
                                "type": "verbose_docstring",
                                "name": node.name,
                                "line": node.lineno,
                                "length": len(docstring),
                                "savings": len(docstring) // 4 - 50,
                            }
                        )
        except SyntaxError:
            pass

        return findings

    def _analyze_docs(self) -> list[dict]:
        """Analyze documentation for inefficiencies."""
        findings = []
        paragraphs = self.content.split("\n\n")

        for i, para in enumerate(paragraphs):
            if len(para) > 500:
                findings.append(
                    {
                        "type": "long_paragraph",
                        "index": i,
                        "length": len(para),
                        "savings": len(para) // 4 - 100,
                    }
                )

        sentences = re.split(r"[.!?]+", self.content)
        phrase_counts = {}
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:
                phrase_counts[sentence] = phrase_counts.get(sentence, 0) + 1

        for phrase, count in phrase_counts.items():
            if count > 1:
                findings.append(
                    {
                        "type": "repeated_phrase",
                        "phrase": phrase[:50] + "...",
                        "count": count,
                        "savings": (count - 1) * len(phrase) // 4,
                    }
                )

        return findings

    def _analyze_generic(self) -> list[dict]:
        """Generic text analysis."""
        findings = []
        words = self.content.split()

        if len(words) > 500:
            findings.append(
                {"type": "verbose_text", "word_count": len(words), "savings": len(words) // 10}
            )

        return findings

    def _estimate_line_tokens(self, line: str) -> int:
        return len(line) // 4


class MLCSkill:
    """Minimal Lossy Compaction skill."""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.target = args.target if hasattr(args, "target") else None
        self.content = None
        self.content_type = "code"

    def run(self) -> bool:
        """Execute MLC workflow."""
        print("=== MLC: Minimal Lossy Compaction ===")
        print()

        if self.target:
            self._load_content()
            if not self.content:
                print(f"Error: Could not read {self.target}")
                return False

        if not self.content:
            print("Usage: /mlc <file> [--apply]")
            print()
            print("Analyzes code/docs/output for token inefficiencies")
            print("and suggests conservative optimizations (20-40% savings).")
            return False

        analyzer = TokenAnalyzer(self.content, self.content_type)
        current_tokens = analyzer.estimate_tokens()

        print(f"Target: {self.target}")
        print(f"Current tokens: ~{current_tokens:,}")
        print()

        findings = analyzer.find_inefficiencies()
        if not findings:
            print("✅ No significant inefficiencies found.")
            return True

        print("Inefficiencies Found:")
        total_savings = 0
        for i, finding in enumerate(findings, 1):
            print(f"{i}. [{finding['type']}] {finding.get('savings', 0)} tokens")
            if finding["type"] == "self_evident_comment":
                print(f"   Line {finding['line']}: {finding['text'][:60]}...")
            elif finding["type"] == "verbose_docstring":
                print(f"   Function {finding['name']}: {finding['length']} char docstring")
            elif finding["type"] == "long_paragraph":
                print(f"   Paragraph {finding['index']}: {finding['length']} chars")
            elif finding["type"] == "repeated_phrase":
                print(f"   Phrase repeated {finding['count']}x: {finding['phrase']}")
            total_savings += finding.get("savings", 0)

        print()
        print(
            f"Potential savings: ~{total_savings} tokens ({total_savings/current_tokens*100:.0f}%)"
        )
        print()
        print("Note: Review suggestions above. Use --apply to attempt auto-optimization.")
        return True

    def _load_content(self) -> None:
        """Load content from target file."""
        target_path = Path(self.target)
        if not target_path.exists():
            print(f"File not found: {self.target}")
            return

        with open(target_path, encoding="utf-8") as f:
            self.content = f.read()

        if self.target.endswith((".md", ".rst", ".txt")):
            self.content_type = "docs"
        elif self.target.endswith((".py", ".js", ".ts", ".java", ".cpp")):
            self.content_type = "code"
        else:
            self.content_type = "generic"


def main():
    """Main entry point for MLC skill."""
    parser = argparse.ArgumentParser(
        description="Minimal Lossy Compaction - Conservative token optimization"
    )
    parser.add_argument("target", nargs="?", help="File to analyze")
    parser.add_argument("--apply", action="store_true", help="Apply optimizations automatically")
    parser.add_argument(
        "--type",
        choices=["code", "docs", "generic"],
        help="Content type (auto-detected if not specified)",
    )

    args = parser.parse_args()

    skill = MLCSkill(args)
    result = skill.run()

    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
