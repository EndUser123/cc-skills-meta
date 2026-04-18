#!/usr/bin/env python3
"""
Output formatting for reflection results.
Supports verbose (decorated) and concise (clean markdown) modes.
"""


class OutputFormatter:
    """Format reflection output in verbose or concise mode."""

    def __init__(self, mode: str = "verbose"):
        """Initialize formatter.

        Args:
            mode: 'verbose' for decorated output, 'concise' for clean markdown
        """
        self.mode = mode

    def format_final_summary(
        self,
        skills_updated: int,
        lessons_stored: int,
        signals_by_skill: dict[str, list[dict]],
        approved_changes: list[dict],
        improvement_recommendations: list[dict] = None,
    ) -> None:
        """Print final reflection summary.

        Args:
            skills_updated: Number of skills successfully updated
            lessons_stored: Number of lessons stored to CKS
            signals_by_skill: All detected signals grouped by skill
            approved_changes: Changes that were approved and applied
            improvement_recommendations: Optional improvement suggestions
        """
        if self.mode == "verbose":
            self._format_verbose_summary(
                skills_updated,
                lessons_stored,
                signals_by_skill,
                approved_changes,
                improvement_recommendations,
            )
        else:
            self._format_concise_summary(
                skills_updated,
                lessons_stored,
                signals_by_skill,
                approved_changes,
                improvement_recommendations,
            )

    def _format_verbose_summary(
        self,
        skills_updated: int,
        lessons_stored: int,
        signals_by_skill: dict[str, list[dict]],
        approved_changes: list[dict],
        improvement_recommendations: list[dict] = None,
    ) -> None:
        """Print verbose formatted summary with decorations."""
        separator = "═" * 60
        print(f"\n{separator}")
        print("📊 SESSION REFLECTION COMPLETE")
        print(f"{separator}\n")

        # Session summary
        print("📅 Session Summary:")
        print("─" * 60)
        print(f"1. Skills updated: {skills_updated}")
        print(f"2. Lessons stored to CKS: {lessons_stored}")
        print(f"3. Signals detected in {len(signals_by_skill)} skill(s)")

        # Count by confidence
        total_high = sum(
            len([s for s in signals if s.get("confidence") == "HIGH"])
            for signals in signals_by_skill.values()
        )
        total_medium = sum(
            len([s for s in signals if s.get("confidence") == "MEDIUM"])
            for signals in signals_by_skill.values()
        )
        total_low = sum(
            len([s for s in signals if s.get("confidence") == "LOW"])
            for signals in signals_by_skill.values()
        )

        item_num = 4
        if total_high:
            print(f"{item_num}. High-confidence corrections: {total_high}")
            item_num += 1
        if total_medium:
            print(f"{item_num}. Medium-confidence approvals: {total_medium}")
            item_num += 1
        if total_low:
            print(f"{item_num}. Low-confidence observations: {total_low}")
            item_num += 1

        print()

        # User corrections (updates to SKILL.md files)
        if skills_updated > 0:
            print("─" * 60)
            print("🎯 USER CORRECTIONS (SKILL.md - auto-saved)")
            print("─" * 60)
            correction_num = 1
            for change in approved_changes:
                skill_name = change.get("skill_name", "unknown")
                proposed = change.get("proposed_updates", {})

                for signal in proposed.get("high_confidence", []):
                    description = signal.get("description", "")
                    old_approach = signal.get("old_approach", "")
                    new_approach = signal.get("new_approach", "")

                    if description:
                        print(f"{correction_num}. {description}")
                        if old_approach and new_approach:
                            print(f"   Don't: {old_approach[:60]}...")
                            print(f"   Do: {new_approach[:60]}...")
                        print(f"   → Updated in: {skill_name}/SKILL.md")
                        print()
                        correction_num += 1

        # Lessons stored to CKS (semantic search)
        if lessons_stored > 0:
            print("─" * 60)
            print("💡 TECHNICAL LEARNINGS (CKS - auto-saved)")
            print("─" * 60)
            lesson_num = 1
            for change in approved_changes:
                skill_name = change.get("skill_name", "unknown")
                proposed = change.get("proposed_updates", {})

                for confidence_level in ["high_confidence", "medium_confidence", "low_confidence"]:
                    for signal in proposed.get(confidence_level, []):
                        content = signal.get("content", "")
                        if content and len(content) >= 20:
                            signal_type = signal.get("type", "correction")
                            confidence = signal.get("confidence_score", 0.5)

                            # Map to severity
                            if confidence >= 0.85:
                                severity = "critical"
                            elif confidence >= 0.70:
                                severity = "important"
                            else:
                                severity = "nice-to-know"

                            # Show full content with context if available
                            print(f"{lesson_num}. [{severity.upper()}] {content}")
                            lesson_num += 1

            # Storage confirmation
            print()
            print(f"✓ Stored {lessons_stored} lesson(s) to CKS")
            print()

        # Pre-mortem risks (if substantial work was done)
        if skills_updated >= 1 or lessons_stored >= 3:
            print("─" * 60)
            print("⚠️  PRE-MORTEM RISKS (Critical-High - Next Steps)")
            print("─" * 60)
            print("1. [RISK:9] Stored lessons become stale or outdated")
            print("   Prevent: Review CKS quarterly with /search to validate relevance")
            print()
            print("2. [RISK:7] CKS storage fails silently")
            print("   Prevent: Check lesson count after reflection, verify storage succeeded")
            print()
            print("3. [RISK:6] Skill updates break existing functionality")
            print("   Prevent: Test skills after reflection before next session")
            print()

        # Improvement recommendations (if any)
        if improvement_recommendations:
            print("─" * 60)
            print("✅ IMPROVEMENT RECOMMENDATIONS (Next Steps)")
            print("─" * 60)

            # Group by category
            categories = {}
            for rec in improvement_recommendations:
                category = rec.get("category", "General")
                if category not in categories:
                    categories[category] = []
                categories[category].append(rec)

            global_num = 1
            for category, items in categories.items():
                print(f"{category}:")
                for item in items:
                    print(f"{global_num}. {item.get('description', '')}")
                    global_num += 1
                print()

        # Next steps
        print("─" * 60)
        print("📋 NEXT STEPS")
        print("─" * 60)
        print("1. Review updated skills in ~/.claude/skills/")
        print("2. Test changes to verify they work as expected")
        print("3. Run /learn to capture additional lessons from this session")
        step_num = 4
        if lessons_stored > 0:
            print(f"{step_num}. Query CKS with /search to retrieve stored lessons")
            step_num += 1
        if skills_updated >= 1 or lessons_stored >= 3:
            print(f"{step_num}. Review pre-mortem risks above (Critical-High)")
            step_num += 1
        if improvement_recommendations:
            print(f"{step_num}. Review improvement recommendations above")
        print(f"{separator}\n")

    def _format_concise_summary(
        self,
        skills_updated: int,
        lessons_stored: int,
        signals_by_skill: dict[str, list[dict]],
        approved_changes: list[dict],
        improvement_recommendations: list[dict] = None,
    ) -> None:
        """Print concise formatted summary (clean markdown)."""
        print("\n## Session Reflection Complete")

        # What happened
        print("\n### What Happened")
        print(f"1. Skills updated: {skills_updated}")
        print(f"2. Lessons stored to CKS: {lessons_stored}")
        print(f"3. Signals detected in {len(signals_by_skill)} skill(s)")

        # User corrections (SKILL.md updates)
        if skills_updated > 0:
            print("\n### User Corrections (SKILL.md - auto-saved)")
            correction_num = 1
            for change in approved_changes:
                skill_name = change.get("skill_name", "unknown")
                proposed = change.get("proposed_updates", {})

                for signal in proposed.get("high_confidence", []):
                    description = signal.get("description", "")
                    old_approach = signal.get("old_approach", "")
                    new_approach = signal.get("new_approach", "")

                    if description:
                        print(f"{correction_num}. {description}")
                        if old_approach and new_approach:
                            print(f"   Don't: {old_approach[:60]}...")
                            print(f"   Do: {new_approach[:60]}...")
                        print(f"   → {skill_name}/SKILL.md")
                        print()
                        correction_num += 1

        # Lessons stored to CKS
        if lessons_stored > 0:
            print("\n### Technical Learnings (CKS - auto-saved)")
            lesson_num = 1
            for change in approved_changes:
                skill_name = change.get("skill_name", "unknown")
                proposed = change.get("proposed_updates", {})

                for confidence_level in ["high_confidence", "medium_confidence", "low_confidence"]:
                    for signal in proposed.get(confidence_level, []):
                        content = signal.get("content", "")
                        if content and len(content) >= 20:
                            print(f"{lesson_num}. {content}")
                            lesson_num += 1

            # Storage confirmation
            print(f"\n✓ Stored {lessons_stored} lesson(s) to CKS")
            print()

        # Pre-mortem risks (if substantial work was done)
        if skills_updated >= 1 or lessons_stored >= 3:
            print("\n### Pre-Mortem Risks (Critical-High - Next Steps)")
            print("1. [RISK:9] Stored lessons become stale or outdated")
            print("   Prevent: Review CKS quarterly with /search to validate relevance")
            print("2. [RISK:7] CKS storage fails silently")
            print("   Prevent: Check lesson count after reflection, verify storage succeeded")
            print("3. [RISK:6] Skill updates break existing functionality")
            print("   Prevent: Test skills after reflection before next session")

        # Improvement recommendations (if any)
        if improvement_recommendations:
            print("\n### Improvement Recommendations (Next Steps)")

            # Group by category
            categories = {}
            for rec in improvement_recommendations:
                category = rec.get("category", "General")
                if category not in categories:
                    categories[category] = []
                categories[category].append(rec)

            global_num = 1
            for category, items in categories.items():
                print(f"**{category}:**")
                for item in items:
                    print(f"{global_num}. {item.get('description', '')}")
                    global_num += 1
                print()

        # Next steps
        print("\n" + "─" * 60)
        print("📋 NEXT STEPS")
        print("─" * 60)
        print("1. Review updated skills in ~/.claude/skills/")
        print("2. Test changes to verify they work as expected")
        print("3. Run /learn to capture additional lessons from this session")
        step_num = 4
        if lessons_stored > 0:
            print(f"{step_num}. Query CKS with /search to retrieve stored lessons")
            step_num += 1
        if skills_updated >= 1 or lessons_stored >= 3:
            print(f"{step_num}. Review pre-mortem risks above (Critical-High)")
            step_num += 1
        if improvement_recommendations:
            print(f"{step_num}. Review improvement recommendations above")
        print()


def format_signal_summary(signals_by_skill: dict[str, list[dict]]) -> None:
    """Format initial signal detection summary.

    Args:
        signals_by_skill: Signals grouped by skill name
    """
    print("\n## Signals Detected\n")
    for skill, signals in signals_by_skill.items():
        high = len([s for s in signals if s.get("confidence") == "HIGH"])
        medium = len([s for s in signals if s.get("confidence") == "MEDIUM"])
        low = len([s for s in signals if s.get("confidence") == "LOW"])

        print(f"**{skill}**:")
        item_num = 1
        if high:
            print(f"  {item_num}. HIGH: {high} corrections")
            item_num += 1
        if medium:
            print(f"  {item_num}. MEDIUM: {medium} approvals")
            item_num += 1
        if low:
            print(f"  {item_num}. LOW: {low} observations")
            item_num += 1
    print()
