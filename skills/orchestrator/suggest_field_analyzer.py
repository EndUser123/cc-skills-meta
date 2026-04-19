"""
Suggest Field Analyzer

Automatically discovers and recommends suggest fields for skills based on:
1. Text analysis (skill mentions in SKILL.md)
2. Category clustering
3. Existing usage patterns

Usage:
    python suggest_field_analyzer.py --analyze
    python suggest_field_analyzer.py --suggest-for /skill-name
    python suggest_field_analyzer.py --fix-missing
"""

from __future__ import annotations

import re
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import Counter, defaultdict
from dataclasses import dataclass


@dataclass
class SkillInfo:
    """Information about a skill."""
    name: str
    path: Path
    category: str
    description: str
    has_suggest: bool
    current_suggests: List[str]
    mentioned_skills: Set[str]
    content: str


class SuggestFieldAnalyzer:
    """Analyze skills to recommend suggest fields."""

    def __init__(self, skills_path: Path = None):
        self.skills_path = skills_path or Path("P:/.claude/skills")
        self.skills: Dict[str, SkillInfo] = {}
        self.category_map: Dict[str, List[str]] = defaultdict(list)
        self.reverse_mentions: Dict[str, Set[str]] = defaultdict(set)  # who mentions me

    def load_all_skills(self) -> None:
        """Load and parse all skill files."""
        for skill_dir in self.skills_path.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue

            skill_name = f"/{skill_dir.name}"
            info = self._parse_skill(skill_name, skill_file)
            self.skills[skill_name] = info
            self.category_map[info.category].append(skill_name)

            # Track reverse mentions
            for mentioned in info.mentioned_skills:
                self.reverse_mentions[mentioned].add(skill_name)

    def _parse_skill(self, skill_name: str, skill_file: Path) -> SkillInfo:
        """Parse a single SKILL.md file."""
        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return SkillInfo(
                name=skill_name,
                path=skill_file,
                category="unknown",
                description="",
                has_suggest=False,
                current_suggests=[],
                mentioned_skills=set(),
                content=""
            )

        # Parse frontmatter
        metadata = {}
        if content.startswith('---'):
            end_marker = content.find('\n---\n', 3)
            if end_marker != -1:
                frontmatter = content[3:end_marker]
                metadata = yaml.safe_load(frontmatter) or {}

        # Extract fields
        category = metadata.get('category', 'unknown')
        description = metadata.get('description', '')
        suggests = metadata.get('suggest', [])
        if isinstance(suggests, str):
            suggests = [suggests]
        suggests = [s if s.startswith('/') else f'/{s}' for s in suggests]

        # Find mentioned skills in content
        mentioned = self._extract_mentioned_skills(content)

        return SkillInfo(
            name=skill_name,
            path=skill_file.parent,
            category=category,
            description=description,
            has_suggest=bool(suggests),
            current_suggests=suggests,
            mentioned_skills=mentioned,
            content=content
        )

    def _extract_mentioned_skills(self, content: str) -> Set[str]:
        """Extract skill mentions from content."""
        # Find patterns like /skill-name or ` /skill-name `
        pattern = r'/(?:[a-z0-9]+(?:-[a-z0-9]+)*)'
        matches = re.findall(pattern, content.lower())

        # Filter out common false positives
        false_positives = {
            '/dev', '/src', '/usr', '/home', '/etc', '/var', '/opt',
            '/bin', '/sbin', '/lib', '/tmp', '/root',
            'https://', 'http://', '://'
        }

        mentioned = set()
        for match in matches:
            if match not in false_positives and len(match) > 2:
                # Normalize
                mentioned.add(match)

        return mentioned

    def analyze_missing_suggests(self) -> List[Tuple[str, List[str]]]:
        """Find skills missing suggest fields and recommend additions."""
        missing = []

        for skill_name, info in self.skills.items():
            if info.has_suggest:
                continue

            recommendations = self._recommend_suggests_for(skill_name)
            if recommendations:
                missing.append((skill_name, recommendations))


    def _recommend_suggests_for(self, skill_name: str) -> List[str]:
        """Generate suggest recommendations for a skill."""
        info = self.skills.get(skill_name)
        if not info:
            return []

        recommendations = []

        # 1. Skills mentioned in content
        for mentioned in info.mentioned_skills:
            if mentioned in self.skills and mentioned != skill_name:
                recommendations.append(mentioned)

        # 2. Skills in same category (frequently used together)
        same_category = [s for s in self.category_map.get(info.category, [])
                        if s != skill_name and s in self.skills]
        # Limit to top 3 by how often they're suggested by others
        same_category_sorted = sorted(
            same_category,
            reverse=True
        )[:3]
        recommendations.extend(same_category_sorted)

        # 3. Remove duplicates and sort
        recommendations = sorted(set(recommendations))

        # Limit to 5 recommendations
        return recommendations[:5]

    def suggest_for(self, skill_name: str) -> Dict[str, any]:
        """Get detailed suggestions for a specific skill."""
        # Strip leading/trailing whitespace
        skill_name = skill_name.strip()

        # Ensure skill name starts with /
        if not skill_name.startswith('/'):
            skill_name = f'/{skill_name}'

        info = self.skills.get(skill_name)
        if not info:
            return {"error": f"Skill {skill_name} not found"}

        recommendations = self._recommend_suggests_for(skill_name)

        # Build analysis
        return {
            "skill": skill_name,
            "category": info.category,
            "current_suggests": info.current_suggests,
            "recommended_additions": recommendations,
            "mentioned_in_content": sorted(info.mentioned_skills),
            "same_category_skills": [s for s in self.category_map.get(info.category, [])
                                    if s != skill_name],
            "suggested_by_count": len(self.reverse_mentions.get(skill_name, set()))
        }

    def get_fix_candidates(self) -> List[Dict[str, any]]:
        """Get skills that can be automatically fixed."""
        candidates = []

        for skill_name, recommendations in self.analyze_missing_suggests():
            if recommendations:
                info = self.skills[skill_name]
                candidates.append({
                    "skill": skill_name,
                    "path": info.path / "SKILL.md",
                    "recommendations": recommendations,
                    "reason": self._explain_recommendation(skill_name, recommendations)
                })

        return candidates

    def _explain_recommendation(self, skill_name: str, recommendations: List[str]) -> str:
        """Explain why these skills are recommended."""
        info = self.skills[skill_name]
        reasons = []

        mentioned = set(recommendations) & info.mentioned_skills
        if mentioned:
            reasons.append(f"mentioned in content: {', '.join(sorted(mentioned))}")

        category = info.category
        same_category = self.category_map.get(category, [])
        category_recs = set(recommendations) & set(same_category)
        if category_recs:
            reasons.append(f"same category ({category}): {', '.join(sorted(category_recs))}")

        return "; ".join(reasons) if reasons else "based on usage patterns"

    def generate_fix_yaml(self, skill_name: str, suggestions: List[str]) -> str:
        """Generate YAML snippet to add suggest field."""
        return f"suggest:\n{chr(10).join(f'  - {s}' for s in suggestions)}"

    def print_analysis(self) -> None:
        """Print analysis summary."""
        print("=" * 60)
        print("SUGGEST FIELD ANALYZER")
        print("=" * 60)

        total = len(self.skills)
        with_suggest = sum(1 for s in self.skills.values() if s.has_suggest)
        without_suggest = total - with_suggest

        print(f"\nTotal skills: {total}")
        print(f"With suggest fields: {with_suggest}")
        print(f"Missing suggest fields: {without_suggest}")

        # Category breakdown
        print("\n--- Skills by Category ---")
        for category, skills in sorted(self.category_map.items()):
            if category == "unknown":
                continue
            print(f"{category:30} {len(skills):3} skills")

        # Most referenced skills
        print("\n--- Most Referenced Skills ---")
        referenced = sorted(
            [(name, len(others)) for name, others in self.reverse_mentions.items()],
            reverse=True
        )[:15]
        for name, count in referenced:
            print(f"  {name:30} referenced by {count:2} skills")

        # Missing suggests
        missing = self.analyze_missing_suggests()
        if missing:
            print(f"\n--- {len(missing)} Skills Missing Suggest Fields ---")
            for skill_name, recommendations in missing:
                print(f"\n{skill_name}:")
                print(f"  Recommended: {', '.join(recommendations)}")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze and fix suggest fields")
    parser.add_argument("--analyze", action="store_true", help="Run full analysis")
    parser.add_argument("--suggest-for", type=str, help="Get suggestions for specific skill")
    parser.add_argument("--fix-missing", action="store_true", help="Show fixes for missing suggest fields")
    parser.add_argument("--skills-path", type=str, default="P:/.claude/skills",
                       help="Path to skills directory")

    args = parser.parse_args()

    analyzer = SuggestFieldAnalyzer(Path(args.skills_path))
    analyzer.load_all_skills()

    if args.analyze:
        analyzer.print_analysis()

    elif args.suggest_for:
        result = analyzer.suggest_for(args.suggest_for)
        if "error" in result:
            print(f"Error: {result['error']}")
            return 1

        print(f"\n=== Analysis for {result['skill']} ===")
        print(f"Category: {result['category']}")
        print(f"Current suggests: {result['current_suggests'] or '(none)'}")
        print(f"Mentioned in content: {result['mentioned_in_content'] or '(none)'}")
        print(f"Suggested by {result['suggested_by_count']} other skills")
        print(f"\nRecommended additions: {result['recommended_additions']}")
        print(f"Same category skills: {result['same_category_skills']}")

    elif args.fix_missing:
        candidates = analyzer.get_fix_candidates()
        print(f"\n=== {len(candidates)} Skills Can Be Auto-Fixed ===\n")

        for candidate in candidates:
            print(f"Skill: {candidate['skill']}")
            print(f"File: {candidate['path']}")
            print(f"Reason: {candidate['reason']}")
            print(f"Add to frontmatter:")
            print(analyzer.generate_fix_yaml(
                candidate['skill'].lstrip('/'),
                candidate['recommendations']
            ))
            print()

    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
